import asyncio
import base64
import io
import json
import logging
import os
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

import aiohttp
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# -------------------
# --- логирование ---
# -------------------

load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "да"}


LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "").strip()
LOG_SENSITIVE_DATA = env_bool("LOG_SENSITIVE_DATA", True)
LOG_HTTP_BODIES = env_bool("LOG_HTTP_BODIES", False)
LOG_ERROR_HTTP_BODIES = env_bool("LOG_ERROR_HTTP_BODIES", True)


def setup_logging():
    log_level = getattr(logging, LOG_LEVEL_NAME, logging.INFO)
    handlers: List[logging.Handler] = [logging.StreamHandler()]

    if LOG_FILE:
        log_path = Path(LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                filename=log_path,
                maxBytes=5_000_000,
                backupCount=5,
                encoding="utf-8",
            )
        )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,
    )


setup_logging()
logger = logging.getLogger("predlozhaloba_tg_bot")

# --- модели данных ---


class AppealType(str, Enum):
    COMPLAINT = "Жалоба"
    SUGGESTION = "Предложение"
    QUESTION = "Вопрос"
    REQUEST = "Запрос"


class LocationType(str, Enum):
    STUDENT_CAMPUS = "Студгородок"
    DORMITORY = "Общежитие"
    ACADEMIC_BUILDING = "Учебный корпус"
    LIBRARY = "Библиотека"
    CANTEEN = "Столовая"
    SPORTS_COMPLEX = "Спорткомплекс"
    MEDICAL_CENTER = "Медпункт"


LOCATION_TYPE_TO_BACKEND = {
    LocationType.STUDENT_CAMPUS: "STUDENT_CAMPUS",
    LocationType.DORMITORY: "DORMITORY",
    LocationType.ACADEMIC_BUILDING: "ACADEMIC_BUILDING",
    LocationType.LIBRARY: "LIBRARY",
    LocationType.CANTEEN: "CANTEEN",
    LocationType.SPORTS_COMPLEX: "SPORTS_COMPLEX",
    LocationType.MEDICAL_CENTER: "MEDICAL_CENTER",
}


class ProblemCategory(str, Enum):
    ACCOMMODATION = "Расселение"
    BATHROOM = "Санузел"
    ELECTRICITY = "Электрика"
    HEATING = "Отопление"
    CLEANLINESS = "Чистота"
    NOISE = "Шум"
    PLUMBING = "Сантехника"
    FURNITURE = "Мебель"
    INTERNET = "Интернет"
    OTHER = "Другое"


PROBLEM_CATEGORY_TO_BACKEND = {
    ProblemCategory.ACCOMMODATION: "ACCOMMODATION",
    ProblemCategory.BATHROOM: "BATHROOM",
    ProblemCategory.ELECTRICITY: "ELECTRICITY",
    ProblemCategory.HEATING: "HEATING",
    ProblemCategory.CLEANLINESS: "CLEANLINESS",
    ProblemCategory.NOISE: "NOISE",
    ProblemCategory.PLUMBING: "PLUMBING",
    ProblemCategory.FURNITURE: "FURNITURE",
    ProblemCategory.INTERNET: "INTERNET",
    ProblemCategory.OTHER: "OTHER",
}


class Timeframe(str, Enum):
    ONE_DAY = "1 день"
    TWO_DAYS = "2 дня"
    THREE_DAYS = "3 дня"
    FIVE_DAYS = "5 дней"
    ONE_WEEK = "1 неделя"
    TWO_WEEKS = "2 недели"
    ONE_MONTH = "1 месяц"


TIMEFRAME_TO_BACKEND = {
    Timeframe.ONE_DAY: "ONE_DAY",
    Timeframe.TWO_DAYS: "TWO_DAYS",
    Timeframe.THREE_DAYS: "THREE_DAYS",
    Timeframe.FIVE_DAYS: "FIVE_DAYS",
    Timeframe.ONE_WEEK: "ONE_WEEK",
    Timeframe.TWO_WEEKS: "TWO_WEEKS",
    Timeframe.ONE_MONTH: "ONE_MONTH",
}

APPEAL_TYPE_TO_BACKEND = {
    AppealType.COMPLAINT: "COMPLAINT",
    AppealType.SUGGESTION: "SUGGESTION",
    AppealType.QUESTION: "QUESTION",
    AppealType.REQUEST: "REQUEST",
}


class AppealStatus(str, Enum):
    NEW = "Новое"
    IN_PROGRESS = "В обработке"
    RESOLVED = "Решено"
    REJECTED = "Отклонено"


def enum_to_backend(value: Optional[Enum]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, AppealType):
        return APPEAL_TYPE_TO_BACKEND.get(value, value.name)
    if isinstance(value, LocationType):
        return LOCATION_TYPE_TO_BACKEND.get(value, value.name)
    if isinstance(value, ProblemCategory):
        return PROBLEM_CATEGORY_TO_BACKEND.get(value, value.name)
    if isinstance(value, Timeframe):
        return TIMEFRAME_TO_BACKEND.get(value, value.name)
    return value.name


@dataclass
class Appeal:
    type: AppealType
    description: str
    personalDataConsent: bool
    tgUserId: int

    campusLocation: Optional[LocationType] = None
    problemCategory: Optional[ProblemCategory] = None
    timeframe: Optional[Timeframe] = None

    id: Optional[str] = None
    attachments: Optional[List[str]] = None
    contactName: Optional[str] = None
    contactPhone: Optional[str] = None
    contactEmail: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: AppealStatus = AppealStatus.NEW

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": enum_to_backend(self.type),
            "description": self.description,
            "personalDataConsent": self.personalDataConsent,
            "tgUserId": self.tgUserId,
            "campusLocation": enum_to_backend(self.campusLocation),
            "problemCategory": enum_to_backend(self.problemCategory),
            "timeframe": enum_to_backend(self.timeframe),
            "attachments": self.attachments or [],
            "contactName": self.contactName,
            "contactPhone": self.contactPhone,
            "contactEmail": self.contactEmail,
        }
        if self.id is not None:
            data["id"] = self.id
        return {key: value for key, value in data.items() if value is not None}


@dataclass
class RegistrationResult:
    request_ok: bool
    registered: bool
    data: Dict[str, Any] = field(default_factory=dict)


# -----------------
# --- настройки ---
# -----------------

TOKEN = os.getenv("TG_TOKEN")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_APPEAL_STATUS_TOPIC = os.getenv(
    "KAFKA_TOPIC_APPEAL_STATUS_CHANGED", "appeal.status.changed"
)
KAFKA_CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP_ID", "tg-bot-group")
KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
KAFKA_ENABLE_AUTO_COMMIT = env_bool("KAFKA_ENABLE_AUTO_COMMIT", True)


def build_api_base_url() -> str:
    base_url = os.getenv("BACKEND_BASE_URL", "http://app:8080").rstrip("/")
    api_prefix = os.getenv("BACKEND_API_PREFIX", "/api").strip("/")
    return f"{base_url}/{api_prefix}" if api_prefix else base_url


API_BASE_URL = build_api_base_url()
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://localhost:5173").rstrip("/")
REGISTRATION_PATH = os.getenv("REGISTRATION_PATH", "/register")
LOGIN_PATH = os.getenv("LOGIN_PATH", "/login")

HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)

START_BUTTON = "Начать"
CHECK_REGISTRATION_BUTTON = "Проверить регистрацию"
BACK_BUTTON = "Назад"
CANCEL_BUTTON = "Отмена"

if not TOKEN:
    raise ValueError(
        "токен не найден. создайте файл .env и добавьте TG_TOKEN=ваш_токен"
    )

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)


def api_url(path: str) -> str:
    return f"{API_BASE_URL}/{path.lstrip('/')}"


def site_url(path: str) -> str:
    return f"{SITE_BASE_URL}/{path.lstrip('/')}"


def add_query_params(url: str, params: Dict[str, Any]) -> str:
    parsed = urlparse(url)
    current_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    current_params.update({key: str(value) for key, value in params.items()})
    return urlunparse(parsed._replace(query=urlencode(current_params)))


def get_registration_url(tg_user_id: int) -> str:
    return add_query_params(site_url(REGISTRATION_PATH), {"tgUserId": tg_user_id})


def get_login_url(tg_user_id: int) -> str:
    return add_query_params(site_url(LOGIN_PATH), {"tgUserId": tg_user_id})


# -------------
# --- кафка ---
# -------------


async def handle_appeal_status_changed_event(event: Dict[str, Any]) -> None:
    tg_user_id = event.get("tgUserId") or event.get("tg_user_id")
    if tg_user_id is None:
        logger.warning("appeal_status_event_missing_tg_user_id", extra={"event": event})
        return

    try:
        peer_id = int(tg_user_id)
    except (TypeError, ValueError):
        return

    appeal_number = (
        event.get("appealNumber") or event.get("appeal_number") or event.get("appealId")
    )
    old_status_raw = event.get("oldStatus") or event.get("old_status")
    new_status_raw = event.get("newStatus") or event.get("new_status")

    def get_display_status(status_str: Optional[str]) -> Optional[str]:
        if not status_str:
            return None
        try:
            return AppealStatus[status_str].value
        except KeyError:
            return status_str

    old_status = get_display_status(old_status_raw)
    new_status = get_display_status(new_status_raw)

    appeal_number = appeal_number or "?"

    if old_status and new_status:
        text = f'Статус вашей заявки №{appeal_number} изменился с "{old_status}" на "{new_status}".'
    elif new_status:
        text = f'Статус вашей заявки №{appeal_number} изменился на "{new_status}".'
    else:
        text = f"Статус вашей заявки №{appeal_number} был обновлен."

    try:
        await bot.send_message(chat_id=peer_id, text=text)
        logger.info("kafka_status_notification_sent", extra={"peer_id": peer_id})
    except Exception as error:
        logger.error(
            "kafka_status_notification_failed peer_id=%s error=%s", peer_id, error
        )


async def kafka_listener_task() -> None:
    try:
        consumer = AIOKafkaConsumer(
            KAFKA_APPEAL_STATUS_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset=KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=KAFKA_ENABLE_AUTO_COMMIT,
            group_id=KAFKA_CONSUMER_GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
    except Exception as error:
        logger.error("kafka_consumer_init_failed %s", error)
        return

    while True:
        try:
            await consumer.start()
            break
        except Exception as e:
            logger.error("kafka_connection_failed | retrying...", exc_info=e)
            await asyncio.sleep(5)

    try:
        async for message in consumer:
            if isinstance(message.value, dict):
                await handle_appeal_status_changed_event(message.value)
    except Exception as error:
        logger.error("kafka_message_processing_failed %s", error)
    finally:
        await consumer.stop()


# -----------------
# --- состояния ---
# -----------------


class AppealState(StatesGroup):
    WAITING_FOR_TYPE = State()
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_CATEGORY = State()
    WAITING_FOR_TIMEFRAME = State()
    WAITING_FOR_DESCRIPTION = State()
    WAITING_FOR_FILES = State()


# ---------------
# --- мапперы ---
# ---------------

LOCATION_CATEGORIES: Dict[LocationType, List[ProblemCategory]] = {
    LocationType.DORMITORY: [
        ProblemCategory.ACCOMMODATION,
        ProblemCategory.BATHROOM,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.HEATING,
        ProblemCategory.CLEANLINESS,
        ProblemCategory.NOISE,
        ProblemCategory.PLUMBING,
        ProblemCategory.FURNITURE,
        ProblemCategory.INTERNET,
        ProblemCategory.OTHER,
    ],
    LocationType.ACADEMIC_BUILDING: [
        ProblemCategory.BATHROOM,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.HEATING,
        ProblemCategory.CLEANLINESS,
        ProblemCategory.NOISE,
        ProblemCategory.PLUMBING,
        ProblemCategory.FURNITURE,
        ProblemCategory.INTERNET,
        ProblemCategory.OTHER,
    ],
    LocationType.STUDENT_CAMPUS: [
        ProblemCategory.ELECTRICITY,
        ProblemCategory.HEATING,
        ProblemCategory.CLEANLINESS,
        ProblemCategory.NOISE,
        ProblemCategory.PLUMBING,
        ProblemCategory.FURNITURE,
        ProblemCategory.INTERNET,
        ProblemCategory.OTHER,
    ],
    LocationType.LIBRARY: [
        ProblemCategory.CLEANLINESS,
        ProblemCategory.NOISE,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.FURNITURE,
        ProblemCategory.INTERNET,
        ProblemCategory.OTHER,
    ],
    LocationType.CANTEEN: [
        ProblemCategory.CLEANLINESS,
        ProblemCategory.NOISE,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.OTHER,
    ],
    LocationType.SPORTS_COMPLEX: [
        ProblemCategory.CLEANLINESS,
        ProblemCategory.NOISE,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.FURNITURE,
        ProblemCategory.OTHER,
    ],
    LocationType.MEDICAL_CENTER: [
        ProblemCategory.CLEANLINESS,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.FURNITURE,
        ProblemCategory.OTHER,
    ],
}

VALID_TIMEFRAMES = [t.value for t in Timeframe]


def get_categories_for_location(location: LocationType) -> List[ProblemCategory]:
    return LOCATION_CATEGORIES.get(location, [ProblemCategory.OTHER])


def normalize_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "да"}:
            return True
        if normalized in {"false", "0", "no", "n", "нет"}:
            return False
    return None


def unwrap_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    for key in ("userResponseDto", "user_response_dto", "user", "data", "profile"):
        if isinstance(data.get(key), dict):
            return data[key]
    return data


def get_first_present(data: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        if data.get(key) not in (None, ""):
            return str(data[key]).strip()
    return None


def build_full_name(user_data: Dict[str, Any]) -> Optional[str]:
    explicit_name = get_first_present(
        user_data,
        "contact_name",
        "contactName",
        "fullName",
        "full_name",
        "fio",
        "name",
        "displayName",
        "display_name",
    )
    if explicit_name:
        return explicit_name

    name_parts = [
        user_data.get("lastname")
        or user_data.get("lastName")
        or user_data.get("last_name"),
        user_data.get("firstname")
        or user_data.get("firstName")
        or user_data.get("first_name"),
        user_data.get("middlename")
        or user_data.get("middleName")
        or user_data.get("middle_name"),
    ]
    full_name = " ".join(str(part).strip() for part in name_parts if part)
    return full_name or None


def get_user_contact_fields(user_data: Dict[str, Any]) -> Dict[str, Any]:
    user_data = unwrap_user_data(user_data)
    consent = True
    for key in (
        "personal_data_consent",
        "personalDataConsent",
        "dataProcessingConsent",
        "consent",
    ):
        parsed = normalize_bool(user_data.get(key))
        if parsed is not None:
            consent = parsed
            break

    contact_email = get_first_present(
        user_data,
        "contact_email",
        "contactEmail",
        "email",
        "mail",
        "telegram",
        "telegram_username",
        "vk",
        "vk_link",
    )

    return {
        "contactName": build_full_name(user_data),
        "contactPhone": get_first_present(
            user_data, "contact_phone", "contactPhone", "phone", "phoneNumber"
        ),
        "contactEmail": contact_email,
        "personalDataConsent": consent,
    }


# -----------
# --- api ---
# -----------

access_tokens: Dict[int, str] = {}
verified_users: set[int] = set()
registration_intro_sent_users: set[int] = set()


async def read_response_payload(response: aiohttp.ClientResponse) -> Any:
    text = (await response.text()).strip()
    if not text:
        return None
    parsed_bool = normalize_bool(text)
    if parsed_bool is not None:
        return parsed_bool
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def get_user_profile(tg_user_id: int) -> Optional[Dict[str, Any]]:
    access_token = access_tokens.get(tg_user_id)
    if not access_token:
        return None
    url = api_url("/user/me")
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                return await read_response_payload(response)
    except Exception:
        return None


def parse_registration_payload(
    payload: Any, tg_user_id: Optional[int] = None
) -> RegistrationResult:
    if isinstance(payload, (bool, str)):
        return RegistrationResult(
            request_ok=True, registered=bool(normalize_bool(payload)), data={}
        )

    if isinstance(payload, dict):
        registered = False
        for key in ("exists", "registered", "isRegistered", "success"):
            parsed = normalize_bool(payload.get(key))
            if parsed is not None:
                registered = parsed
                break

        user_data = unwrap_user_data(payload)
        if not registered and user_data:
            registered = True

        if tg_user_id and registered and payload.get("accessToken"):
            access_tokens[tg_user_id] = payload.get("accessToken")

        return RegistrationResult(
            request_ok=True, registered=registered, data=user_data if registered else {}
        )

    return RegistrationResult(request_ok=True, registered=False, data={})


async def check_user_registration(tg_user_id: int) -> RegistrationResult:
    url = api_url("/user/check")
    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.get(url, params={"tgUserId": tg_user_id}) as response:
                if response.status != 200:
                    return RegistrationResult(
                        request_ok=False, registered=False, data={}
                    )
                payload = await read_response_payload(response)
                return parse_registration_payload(payload, tg_user_id)
    except Exception:
        return RegistrationResult(request_ok=False, registered=False, data={})


async def send_to_backend(appeal: Appeal) -> Tuple[bool, Optional[int]]:
    url = api_url("/appeals")
    body = appeal.to_dict()
    access_token = access_tokens.get(appeal.tgUserId)
    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.post(url, json=body, headers=headers) as response:
                if response.status in (200, 201):
                    response_text = await response.text()
                    appeal_number = None
                    try:
                        payload = json.loads(response_text)
                        if isinstance(payload, dict):
                            appeal_number = payload.get("appealNumber") or payload.get(
                                "appeal_number"
                            )
                            if not appeal_number and isinstance(
                                payload.get("data"), dict
                            ):
                                appeal_number = payload["data"].get(
                                    "appealNumber"
                                ) or payload["data"].get("appeal_number")
                    except json.JSONDecodeError:
                        pass
                    return True, appeal_number
                return False, None
    except Exception:
        return False, None


async def build_appeal_from_payload(
    payload: Dict[str, Any], tg_user_id: int
) -> Tuple[Optional[Appeal], RegistrationResult]:
    registration = await check_user_registration(tg_user_id)
    if not registration.request_ok or not registration.registered:
        return None, registration

    user_profile_data = await get_user_profile(tg_user_id)
    contact_source_data = user_profile_data if user_profile_data else registration.data
    user_fields = get_user_contact_fields(contact_source_data)

    try:
        appeal_type = AppealType(payload.get("type"))
    except ValueError:
        appeal_type = AppealType.SUGGESTION

    campusLocation = payload.get("campusLocation")
    if campusLocation:
        campusLocation = LocationType(campusLocation)
    problemCategory = payload.get("problemCategory")
    if problemCategory:
        problemCategory = ProblemCategory(problemCategory)
    timeframe = payload.get("timeframe")
    if timeframe:
        timeframe = Timeframe(timeframe)

    if appeal_type != AppealType.COMPLAINT:
        if not campusLocation:
            campusLocation = LocationType.STUDENT_CAMPUS
        if not problemCategory:
            problemCategory = ProblemCategory.OTHER

    appeal = Appeal(
        type=appeal_type,
        description=str(payload.get("description", "")).strip(),
        personalDataConsent=user_fields.get("personalDataConsent", True),
        tgUserId=tg_user_id,
        campusLocation=campusLocation,
        problemCategory=problemCategory,
        timeframe=timeframe,
        attachments=payload.get("attachments", []),
        contactName=user_fields.get("contactName"),
        contactPhone=user_fields.get("contactPhone"),
        contactEmail=user_fields.get("contactEmail"),
    )
    return appeal, registration


# ------------------
# --- клавиатуры ---
# ------------------


def get_registration_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=CHECK_REGISTRATION_BUTTON))
    return builder.as_markup(resize_keyboard=True)


def get_start_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=START_BUTTON))
    builder.row(KeyboardButton(text=CHECK_REGISTRATION_BUTTON))
    return builder.as_markup(resize_keyboard=True)


def add_navigation(builder: ReplyKeyboardBuilder) -> ReplyKeyboardMarkup:
    builder.row(KeyboardButton(text=BACK_BUTTON), KeyboardButton(text=CANCEL_BUTTON))
    return builder.as_markup(resize_keyboard=True)


def get_navigation_kb() -> ReplyKeyboardMarkup:
    return add_navigation(ReplyKeyboardBuilder())


def get_type_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=AppealType.COMPLAINT.value),
        KeyboardButton(text=AppealType.SUGGESTION.value),
    )
    builder.row(
        KeyboardButton(text=AppealType.QUESTION.value),
        KeyboardButton(text=AppealType.REQUEST.value),
    )
    builder.row(KeyboardButton(text=CANCEL_BUTTON))
    return builder.as_markup(resize_keyboard=True)


def get_location_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for loc in [
        LocationType.STUDENT_CAMPUS,
        LocationType.DORMITORY,
        LocationType.ACADEMIC_BUILDING,
        LocationType.LIBRARY,
        LocationType.CANTEEN,
        LocationType.SPORTS_COMPLEX,
        LocationType.MEDICAL_CENTER,
    ]:
        builder.add(KeyboardButton(text=loc.value))
    builder.adjust(2)
    return add_navigation(builder)


def get_category_kb(location: LocationType) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    categories = get_categories_for_location(location)
    for cat in categories:
        builder.add(KeyboardButton(text=cat.value))
    builder.adjust(2)
    return add_navigation(builder)


def get_timeframe_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for tf in VALID_TIMEFRAMES:
        builder.add(KeyboardButton(text=tf))
    builder.adjust(2)
    return add_navigation(builder)


def get_files_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Пропустить"))
    builder.row(KeyboardButton(text=BACK_BUTTON))
    return builder.as_markup(resize_keyboard=True)


# -------------------
# --- регистрация ---
# -------------------


async def send_registration_intro(message: Message):
    tg_user_id = message.from_user.id
    registration_intro_sent_users.add(tg_user_id)
    registration_url = get_registration_url(tg_user_id)
    login_url = get_login_url(tg_user_id)

    text = (
        "Добро пожаловать в модуль «Предложалоба».\n\n"
        "Перед отправкой обращения нужно зарегистрироваться на сайте.\n\n"
        f"Ссылка на регистрацию:\n{registration_url}\n\n"
        f"Если вы уже зарегистрированы на сайте, то привяжите свою учетную запись к Telegram по следующей ссылке:\n{login_url}\n\n"
        "После регистрации нажмите «Проверить регистрацию»."
    )
    await message.answer(text, reply_markup=get_registration_kb())


async def process_registration_check(message: Message, state: FSMContext):
    tg_user_id = message.from_user.id
    current_state = await state.get_state()

    if tg_user_id in verified_users:
        if current_state == AppealState.WAITING_FOR_TYPE.state:
            await message.answer(
                "Регистрация уже подтверждена. Выберите тип обращения:",
                reply_markup=get_type_kb(),
            )
        elif current_state:
            await message.answer(
                "Регистрация уже подтверждена. Продолжайте текущий шаг или нажмите «Отмена».",
                reply_markup=get_navigation_kb(),
            )
        else:
            await state.set_state(AppealState.WAITING_FOR_TYPE)
            await message.answer(
                "Регистрация подтверждена.\nВыберите тип обращения:",
                reply_markup=get_type_kb(),
            )
        return

    result = await check_user_registration(tg_user_id)

    if not result.request_ok:
        await message.answer(
            "Возникла ошибка при проверке регистрации. Попробуйте позже.",
            reply_markup=get_registration_kb(),
        )
        return

    if not result.registered:
        verified_users.discard(tg_user_id)
        reg_url = get_registration_url(tg_user_id)
        log_url = get_login_url(tg_user_id)
        await message.answer(
            f"Регистрация не найдена.\n\nСсылка на регистрацию:\n{reg_url}\n\nИли привяжите аккаунт:\n{log_url}",
            reply_markup=get_registration_kb(),
        )
        return

    verified_users.add(tg_user_id)

    if current_state == AppealState.WAITING_FOR_TYPE.state:
        await message.answer(
            "Регистрация подтверждена. Выберите тип обращения:",
            reply_markup=get_type_kb(),
        )
    elif current_state:
        await message.answer(
            "Регистрация подтверждена. Продолжайте текущий шаг или нажмите «Отмена».",
            reply_markup=get_navigation_kb(),
        )
    else:
        await state.set_state(AppealState.WAITING_FOR_TYPE)
        await message.answer(
            "Регистрация подтверждена.\nВыберите тип обращения:",
            reply_markup=get_type_kb(),
        )


# -----------------
# --- навигация ---
# -----------------


@router.message(F.text == CANCEL_BUTTON)
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено. Нажмите «Начать», чтобы начать заново.",
        reply_markup=get_start_kb(),
    )


@router.message(F.text == CHECK_REGISTRATION_BUTTON)
async def check_reg_handler(message: Message, state: FSMContext):
    await process_registration_check(message, state)


@router.message(F.text == BACK_BUTTON)
async def back_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        return

    payload = await state.get_data()
    appeal_type = payload.get("type")

    if current_state == AppealState.WAITING_FOR_LOCATION.state:
        await state.set_state(AppealState.WAITING_FOR_TYPE)
        await message.answer("Выберите тип обращения:", reply_markup=get_type_kb())
    elif current_state == AppealState.WAITING_FOR_CATEGORY.state:
        await state.set_state(AppealState.WAITING_FOR_LOCATION)
        await message.answer(
            "Выберите локацию проблемы:", reply_markup=get_location_kb()
        )
    elif current_state == AppealState.WAITING_FOR_TIMEFRAME.state:
        location = LocationType(payload.get("campusLocation"))
        await state.set_state(AppealState.WAITING_FOR_CATEGORY)
        await message.answer(
            "Выберите категорию проблемы:", reply_markup=get_category_kb(location)
        )
    elif current_state == AppealState.WAITING_FOR_DESCRIPTION.state:
        if appeal_type == AppealType.COMPLAINT.value:
            await state.set_state(AppealState.WAITING_FOR_TIMEFRAME)
            await message.answer(
                "Укажите ориентировочные сроки:", reply_markup=get_timeframe_kb()
            )
        else:
            await state.set_state(AppealState.WAITING_FOR_TYPE)
            await message.answer("Выберите тип обращения:", reply_markup=get_type_kb())
    elif current_state == AppealState.WAITING_FOR_FILES.state:
        await state.set_state(AppealState.WAITING_FOR_DESCRIPTION)
        await message.answer(
            "Опишите обращение подробнее:", reply_markup=get_navigation_kb()
        )
    elif current_state == AppealState.WAITING_FOR_TYPE.state:
        await message.answer("Вы уже на первом шаге.", reply_markup=get_type_kb())


# -------------------
# --- обработчики ---
# -------------------


@router.message(CommandStart())
@router.message(F.text.in_({START_BUTTON, "Привет", "предложалоба", "Предложалоба"}))
async def start_handler(message: Message, state: FSMContext):
    if await state.get_state():
        await message.answer(
            "Сначала завершите текущее обращение или нажмите «Отмена».",
            reply_markup=get_navigation_kb(),
        )
        return

    tg_user_id = message.from_user.id
    if tg_user_id not in verified_users:
        await send_registration_intro(message)
    else:
        await state.set_state(AppealState.WAITING_FOR_TYPE)
        await message.answer(
            "Регистрация подтверждена.\nВыберите тип обращения:",
            reply_markup=get_type_kb(),
        )


@router.message(AppealState.WAITING_FOR_TYPE)
async def type_handler(message: Message, state: FSMContext):
    tg_user_id = message.from_user.id
    if tg_user_id not in verified_users:
        await send_registration_intro(message)
        return

    text = message.text
    if text == AppealType.COMPLAINT.value:
        await state.update_data(type=text)
        await state.set_state(AppealState.WAITING_FOR_LOCATION)
        await message.answer(
            "Выберите локацию проблемы:", reply_markup=get_location_kb()
        )
    elif text == AppealType.SUGGESTION.value:
        await state.update_data(type=text)
        await state.set_state(AppealState.WAITING_FOR_DESCRIPTION)
        await message.answer(
            "Опишите суть вашего предложения:", reply_markup=get_navigation_kb()
        )
    elif text == AppealType.QUESTION.value:
        await state.update_data(type=text)
        await state.set_state(AppealState.WAITING_FOR_DESCRIPTION)
        await message.answer(
            "Опишите суть вашего вопроса:", reply_markup=get_navigation_kb()
        )
    elif text == AppealType.REQUEST.value:
        await state.update_data(type=text)
        await state.set_state(AppealState.WAITING_FOR_DESCRIPTION)
        await message.answer(
            "Опишите суть вашего запроса:", reply_markup=get_navigation_kb()
        )
    else:
        await message.answer(
            "Пожалуйста, воспользуйтесь кнопками.", reply_markup=get_type_kb()
        )


@router.message(AppealState.WAITING_FOR_LOCATION)
async def location_handler(message: Message, state: FSMContext):
    try:
        loc = LocationType(message.text)
        await state.update_data(campusLocation=loc.value)
        await state.set_state(AppealState.WAITING_FOR_CATEGORY)
        await message.answer(
            "Выберите категорию проблемы:", reply_markup=get_category_kb(loc)
        )
    except ValueError:
        await message.answer(
            "Выберите локацию из списка.", reply_markup=get_location_kb()
        )


@router.message(AppealState.WAITING_FOR_CATEGORY)
async def category_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    loc = LocationType(data.get("campusLocation"))
    allowed = get_categories_for_location(loc)
    try:
        cat = ProblemCategory(message.text)
        if cat not in allowed:
            raise ValueError
        await state.update_data(problemCategory=cat.value)

        if data.get("type") == AppealType.COMPLAINT.value:
            await state.set_state(AppealState.WAITING_FOR_TIMEFRAME)
            await message.answer(
                "Укажите ориентировочные сроки:", reply_markup=get_timeframe_kb()
            )
        else:
            await state.set_state(AppealState.WAITING_FOR_DESCRIPTION)
            await message.answer(
                "Опишите суть обращения:", reply_markup=get_navigation_kb()
            )
    except ValueError:
        await message.answer(
            "Выберите допустимую категорию из списка.",
            reply_markup=get_category_kb(loc),
        )


@router.message(AppealState.WAITING_FOR_TIMEFRAME)
async def timeframe_handler(message: Message, state: FSMContext):
    if message.text not in VALID_TIMEFRAMES:
        await message.answer(
            "Пожалуйста, воспользуйтесь кнопками.", reply_markup=get_timeframe_kb()
        )
        return
    await state.update_data(timeframe=message.text)
    await state.set_state(AppealState.WAITING_FOR_DESCRIPTION)
    await message.answer(
        "Опишите суть вашей проблемы подробно:", reply_markup=get_navigation_kb()
    )


@router.message(AppealState.WAITING_FOR_DESCRIPTION)
async def description_handler(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer(
            "Описание слишком короткое. Опишите подробнее:",
            reply_markup=get_navigation_kb(),
        )
        return

    await state.update_data(description=message.text)
    payload = await state.get_data()
    tg_user_id = message.from_user.id

    appeal, registration = await build_appeal_from_payload(payload, tg_user_id)
    if not registration.request_ok:
        await message.answer(
            "Возникла ошибка при проверке регистрации. Попробуйте позже.",
            reply_markup=get_navigation_kb(),
        )
        return
    if not registration.registered:
        verified_users.discard(tg_user_id)
        await state.clear()
        reg_url = get_registration_url(tg_user_id)
        await message.answer(
            f"Регистрация не найдена.\n{reg_url}", reply_markup=get_registration_kb()
        )
        return

    await state.set_state(AppealState.WAITING_FOR_FILES)
    await message.answer(
        "📎 Если у вас есть файлы (JPG, PNG, PDF), которые помогут описать проблему, отправьте их.\n\nИли нажмите 'Пропустить', чтобы отправить обращение без файлов:",
        reply_markup=get_files_kb(),
    )


@router.message(AppealState.WAITING_FOR_FILES)
async def files_handler(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await finalize_appeal(message, state)
        return

    payload = await state.get_data()
    attachments = payload.get("attachments", [])
    new_attachments = []

    if message.photo:
        photo = message.photo[-1]
        try:
            file_info = await bot.get_file(photo.file_id)
            file_bytes = io.BytesIO()
            await bot.download_file(file_info.file_path, file_bytes)
            b64 = base64.b64encode(file_bytes.getvalue()).decode("utf-8")
            new_attachments.append(f"data:image/jpeg;base64,{b64}")
        except Exception as e:
            logger.error(f"Error downloading photo: {e}")

    elif message.document:
        doc = message.document
        try:
            file_info = await bot.get_file(doc.file_id)
            file_bytes = io.BytesIO()
            await bot.download_file(file_info.file_path, file_bytes)
            mime = doc.mime_type or "application/octet-stream"
            b64 = base64.b64encode(file_bytes.getvalue()).decode("utf-8")
            new_attachments.append(f"data:{mime};base64,{b64}")
        except Exception as e:
            logger.error(f"Error downloading document: {e}")

    if new_attachments:
        attachments.extend(new_attachments)
        await state.update_data(attachments=attachments)
        await message.answer(
            f"✅ Файлов добавлено. Всего файлов: {len(attachments)}\n\nМожете отправить еще файлы или нажать 'Пропустить' для завершения:",
            reply_markup=get_files_kb(),
        )
    else:
        await message.answer(
            "Пожалуйста, отправьте фото/документ или нажмите 'Пропустить'.",
            reply_markup=get_files_kb(),
        )


async def finalize_appeal(message: Message, state: FSMContext):
    payload = await state.get_data()
    tg_user_id = message.from_user.id

    appeal, registration = await build_appeal_from_payload(payload, tg_user_id)
    if not registration.request_ok or not registration.registered:
        await message.answer(
            "Ошибка регистрации. Обращение не отправлено.", reply_markup=get_start_kb()
        )
        await state.clear()
        return

    if not appeal:
        await message.answer(
            "Ошибка формирования обращения.", reply_markup=get_start_kb()
        )
        await state.clear()
        return

    saved, appeal_number = await send_to_backend(appeal)
    if not saved:
        await message.answer(
            "Возникла ошибка при отправке обращения к серверу. Попробуйте позже.",
            reply_markup=get_files_kb(),
        )
        return

    await state.clear()
    appeal_number_text = f"\nНомер заявки: №{appeal_number}" if appeal_number else ""

    success_text = {
        AppealType.COMPLAINT: f"✅ Ваша жалоба успешно зарегистрирована!{appeal_number_text}",
        AppealType.SUGGESTION: f"✅ Ваше предложение успешно зарегистрировано!{appeal_number_text}",
        AppealType.QUESTION: f"✅ Ваш вопрос успешно зарегистрирован!{appeal_number_text}",
        AppealType.REQUEST: f"✅ Ваш запрос успешно зарегистрирован!{appeal_number_text}",
    }.get(
        appeal.type, f"✅ Ваше обращение успешно зарегистрировано!{appeal_number_text}"
    )

    await message.answer(success_text, reply_markup=get_start_kb())


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    if await state.get_state():
        await message.answer(
            "Пожалуйста, следуйте инструкциям или используйте кнопки «Назад» / «Отмена».",
            reply_markup=get_navigation_kb(),
        )
    else:
        await send_registration_intro(message)


async def main():
    logger.info("Бот 'Предложалоба' (TG) запущен!")
    # Запускаем Kafka в фоне
    asyncio.create_task(kafka_listener_task())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
