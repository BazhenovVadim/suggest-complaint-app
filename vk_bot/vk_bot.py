import asyncio
import base64
import json
import logging
import os
import random
from aiokafka import AIOKafkaConsumer
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from functools import wraps
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import aiohttp
from dotenv import load_dotenv
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, BaseStateGroup

# -------------------
# --- логирование ---
# -------------------

load_dotenv()

# обработка логических переменных окружения в разных форматах 
def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "да"}

# настройки логирования
LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "").strip()
LOG_SENSITIVE_DATA = env_bool("LOG_SENSITIVE_DATA", True)
LOG_HTTP_BODIES = env_bool("LOG_HTTP_BODIES", False)
LOG_ERROR_HTTP_BODIES = env_bool("LOG_ERROR_HTTP_BODIES", True)


def setup_logging():
    log_level = getattr(logging, LOG_LEVEL_NAME, logging.INFO)

    handlers: List[logging.Handler] = [
        logging.StreamHandler(),
    ]

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
logger = logging.getLogger("predlozhaloba_bot")

logger.info(
    "logging_initialized | %s",
    json.dumps(
        {
            "log_level": LOG_LEVEL_NAME,
            "log_file": LOG_FILE or None,
            "log_sensitive_data": LOG_SENSITIVE_DATA,
            "log_http_bodies": LOG_HTTP_BODIES,
            "log_error_http_bodies": LOG_ERROR_HTTP_BODIES,
        },
        ensure_ascii=False,
    ),
)


# --- модели данных ---

# тип обращения
class AppealType(str, Enum):
    COMPLAINT = "Жалоба"
    SUGGESTION = "Предложение"
    QUESTION = "Вопрос"
    REQUEST = "Запрос"

# локация проблемы
class LocationType(str, Enum):
    STUDENT_CAMPUS = "Студгородок"
    DORMITORY = "Общежитие"
    ACADEMIC_BUILDING = "Учебный корпус"
    LIBRARY = "Библиотека"
    CANTEEN = "Столовая"
    SPORTS_COMPLEX = "Спорткомплекс"
    MEDICAL_CENTER = "Медпункт"

# преобразование локации для бэкенда 
LOCATION_TYPE_TO_BACKEND = {
    LocationType.STUDENT_CAMPUS: "STUDENT_CAMPUS",
    LocationType.DORMITORY: "DORMITORY",
    LocationType.ACADEMIC_BUILDING: "ACADEMIC_BUILDING",
    LocationType.LIBRARY: "LIBRARY",
    LocationType.CANTEEN: "CANTEEN",
    LocationType.SPORTS_COMPLEX: "SPORTS_COMPLEX",
    LocationType.MEDICAL_CENTER: "MEDICAL_CENTER",
}

# категория проблемы
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

class AppealStatus(str, Enum):
    NEW = "Новое"
    IN_PROGRESS = "В обработке"
    RESOLVED = "Решено"
    REJECTED = "Отклонено"

# преобразование категории проблемы для бэкенда
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

# сроки
class Timeframe(str, Enum):
    ONE_DAY = "1 день"
    TWO_DAYS = "2 дня"
    THREE_DAYS = "3 дня"
    FIVE_DAYS = "5 дней"
    ONE_WEEK = "1 неделя"
    TWO_WEEKS = "2 недели"
    ONE_MONTH = "1 месяц"

# преобразование сроков для бэкенда
TIMEFRAME_TO_BACKEND = {
    Timeframe.ONE_DAY: "ONE_DAY",
    Timeframe.TWO_DAYS: "TWO_DAYS",
    Timeframe.THREE_DAYS: "THREE_DAYS",
    Timeframe.FIVE_DAYS: "FIVE_DAYS",
    Timeframe.ONE_WEEK: "ONE_WEEK",
    Timeframe.TWO_WEEKS: "TWO_WEEKS",
    Timeframe.ONE_MONTH: "ONE_MONTH",
}

# преобразования типа обращения для бэкенда
APPEAL_TYPE_TO_BACKEND = {
    AppealType.COMPLAINT: "COMPLAINT",
    AppealType.SUGGESTION: "SUGGESTION",
    AppealType.QUESTION: "QUESTION",
    AppealType.REQUEST: "REQUEST",
}

# статус обращения
class AppealStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

# класс для аппила 
# единственное, что мне тут не нравится, что это захардкожено, при любом изменении на бэке надо лезть сюда и всё менять
@dataclass
class Appeal:
    type: AppealType
    description: str
    personalDataConsent: bool
    vkUserId: int

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

    # метод для преобразования обращения  в json для бэкенда
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": enum_to_backend(self.type),
            "description": self.description,
            "personalDataConsent": self.personalDataConsent,
            "campusLocation": enum_to_backend(self.campusLocation),
            "problemCategory": enum_to_backend(self.problemCategory),
            "timeframe": enum_to_backend(self.timeframe),
            "attachments": self.attachments or [],
            "contactName": self.contactName,
            "contactPhone": self.contactPhone,
            "contactEmail": self.contactEmail,
        }

        # если есть айдишник
        if self.id is not None:
            data["id"] = self.id

        # если надо серверные поля
        if APPEAL_SEND_SERVER_FIELDS:
            data["createdAt"] = self.created_at.isoformat()
            data["status"] = enum_to_backend(self.status)

        result = {
            key: value
            for key, value in data.items()
            if value is not None
        }

        log_event(
            logging.DEBUG,
            "appeal_serialized",
            vk_user_id=self.vkUserId,
            appeal_type=self.type,
            payload=safe_payload(result),
        )

        return result

# класс для результатов проверки регистрации 
@dataclass
class RegistrationResult:
    request_ok: bool
    registered: bool
    data: Dict[str, Any] = field(default_factory=dict)

# -----------------
# --- настройки ---
# -----------------

TOKEN = os.getenv("VK_TOKEN")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_APPEAL_STATUS_TOPIC = os.getenv("KAFKA_TOPIC_APPEAL_STATUS_CHANGED", "appeal.status.changed")
KAFKA_CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP_ID", "vk-bot-group")
KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
KAFKA_ENABLE_AUTO_COMMIT = env_bool("KAFKA_ENABLE_AUTO_COMMIT", True)

# функция для построения базового url для обращения к api бэкенда
def build_api_base_url() -> str:
    base_url = os.getenv("BACKEND_BASE_URL", "http://app:8080").rstrip("/")
    api_prefix = os.getenv("BACKEND_API_PREFIX", "/api").strip("/")

    if api_prefix:
        result = f"{base_url}/{api_prefix}"
    else:
        result = base_url

    logger.info(
        "api_base_url_built | %s",
        json.dumps(
            {
                "base_url": base_url,
                "api_prefix": api_prefix,
                "api_base_url": result,
            },
            ensure_ascii=False,
        ),
    )

    return result

# константы для работы с бэкендом
API_BASE_URL = build_api_base_url()
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://localhost:5173").rstrip("/")
REGISTRATION_PATH = os.getenv("REGISTRATION_PATH", "/register")

# формат для отправки енум в бэкенд
APPEAL_ENUM_FORMAT = os.getenv("APPEAL_ENUM_FORMAT", "name").strip().lower()
APPEAL_SEND_SERVER_FIELDS = env_bool("APPEAL_SEND_SERVER_FIELDS", False)

# словарь для хранения access token после регистрации
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)

# тексты кнопок
START_BUTTON = "Начать"
CHECK_REGISTRATION_BUTTON = "Проверить регистрацию"
BACK_BUTTON = "Назад"
CANCEL_BUTTON = "Отмена"

logger.info(
    "configuration_loaded | %s",
    json.dumps(
        {
            "token_configured": bool(TOKEN),
            "api_base_url": API_BASE_URL,
            "site_base_url": SITE_BASE_URL,
            "registration_path": REGISTRATION_PATH,
            "appeal_enum_format": APPEAL_ENUM_FORMAT,
            "appeal_send_server_fields": APPEAL_SEND_SERVER_FIELDS,
            "http_timeout_seconds": HTTP_TIMEOUT_SECONDS,
        },
        ensure_ascii=False,
    ),
)

# проверка наличия токена и создание экземпляра бота
if not TOKEN:
    logger.critical("vk_token_missing")
    raise ValueError("токен не найден. создайте файл .env и добавьте VK_TOKEN=ваш_токен")

bot = Bot(token=TOKEN)
logger.info("bot_instance_created")

# функция для построения полного url для обращения к api бэкенда
def api_url(path: str) -> str:
    result = f"{API_BASE_URL}/{path.lstrip('/')}"

    log_event(
        logging.DEBUG,
        "api_url_created",
        path=path,
        url=result,
    )

    return result

# функция для построения полного url сайта
def site_url(path: str) -> str:
    result = f"{SITE_BASE_URL}/{path.lstrip('/')}"

    log_event(
        logging.DEBUG,
        "site_url_created",
        path=path,
        url=result,
    )

    return result

# -------------
# --- кафка ---
# -------------

# функция для отправки сообщения если изменился статус
async def handle_appeal_status_changed_event(event: Dict[str, Any]) -> None:
    vk_user_id = event.get("vkUserId") or event.get("vk_user_id")
    if vk_user_id is None:
        logger.warning("appeal_status_event_missing_vk_user_id", extra={"event": event})
        return

    try:
        peer_id = int(vk_user_id)
    except (TypeError, ValueError):
        logger.warning(
            "appeal_status_event_invalid_vk_user_id",
            extra={"vk_user_id": vk_user_id, "event": event},
        )
        return

    appeal_number = event.get("appealNumber") or event.get("appeal_number") or event.get("appealId")
    old_status = AppealState(event.get("oldStatus") or event.get("old_status"))
    new_status = AppealState(event.get("newStatus") or event.get("new_status"))

    if appeal_number is None:
        appeal_number = "?"

    if old_status and new_status:
        text = f"Статус вашей заявки №{appeal_number} изменился с {old_status} на {new_status}."
    elif new_status:
        text = f"Статус вашей заявки №{appeal_number} изменился на {new_status}."
    else:
        text = f"Статус вашей заявки №{appeal_number} был обновлен."

    if not TOKEN:
        logger.warning("vk_message_send_skipped_no_token")
        return

    try:
        await bot.api.messages.send(
            peer_id=peer_id,
            message=text,
            random_id=random.randint(0, 2**31 - 1),
        )
        logger.info(
            "kafka_status_notification_sent",
            extra={"peer_id": peer_id, "message": text},
        )
    except Exception as error:
        logger.error(
            "kafka_status_notification_failed peer_id=%s error=%s",
            peer_id,
            error,
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
            logger.info(f"connecting_to_kafka | bootstrap_servers={KAFKA_BOOTSTRAP_SERVERS}")
            await consumer.start()
            logger.info("kafka_listener_started")
            break  
        except Exception as e:
            logger.error("kafka_connection_failed | error=%s | retrying_in_5_seconds...", e)
            await asyncio.sleep(5)  # Ждем 5 секунд и пробуем снова

    try:
        async for message in consumer:
            try:
                event = message.value
                if isinstance(event, dict):
                    await handle_appeal_status_changed_event(event)
                else:
                    logger.warning(
                        "kafka_message_unexpected_value_type",
                        extra={
                            "value_type": type(event).__name__,
                            "raw_value": event,
                        },
                    )
            except Exception as error:
                logger.error("kafka_message_processing_failed %s", error)
    finally:
        await consumer.stop()

# -----------------
# --- состояния ---
# -----------------

class AppealState(BaseStateGroup):
    WAITING_FOR_TYPE = 0
    WAITING_FOR_LOCATION = 1
    WAITING_FOR_CATEGORY = 2
    WAITING_FOR_TIMEFRAME = 3
    WAITING_FOR_DESCRIPTION = 4
    WAITING_FOR_FILES = 5

# ---------------
# --- мапперы ---
# ---------------

# разные категории для разных проблем
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

# сроки для вывода пользователю 
VALID_TIMEFRAMES = [
    Timeframe.ONE_DAY.value,
    Timeframe.TWO_DAYS.value,
    Timeframe.THREE_DAYS.value,
    Timeframe.FIVE_DAYS.value,
    Timeframe.ONE_WEEK.value,
    Timeframe.TWO_WEEKS.value,
    Timeframe.ONE_MONTH.value,
]

# ключи, которые считаются чувствительными и не должны логироваться в открытом виде
SENSITIVE_KEYS = {
    "description",
    "password",
    "contact_name",
    "contactName",
    "fullName",
    "full_name",
    "fio",
    "name",
    "displayName",
    "display_name",
    "contact_phone",
    "contactPhone",
    "phone",
    "phoneNumber",
    "phone_number",
    "contact_email",
    "contactEmail",
    "email",
    "mail",
    "contact",
    "contactLink",
    "contact_link",
    "telegram",
    "telegram_username",
    "telegramUsername",
    "vk",
    "vk_link",
    "vkLink",
    "file_path",
    "filePath",
    "file_name",
    "fileName",
    "registrationUrl",
}

# текст для кнопок бота
BUTTON_TEXTS = {
    START_BUTTON,
    CHECK_REGISTRATION_BUTTON,
    BACK_BUTTON,
    CANCEL_BUTTON,
    AppealType.COMPLAINT.value,
    AppealType.SUGGESTION.value,
    AppealType.QUESTION.value,
    AppealType.REQUEST.value,
    LocationType.STUDENT_CAMPUS.value,
    LocationType.DORMITORY.value,
    LocationType.ACADEMIC_BUILDING.value,
    LocationType.LIBRARY.value,
    LocationType.CANTEEN.value,
    LocationType.SPORTS_COMPLEX.value,
    LocationType.MEDICAL_CENTER.value,
    ProblemCategory.ACCOMMODATION.value,
    ProblemCategory.BATHROOM.value,
    ProblemCategory.ELECTRICITY.value,
    ProblemCategory.HEATING.value,
    ProblemCategory.CLEANLINESS.value,
    ProblemCategory.NOISE.value,
    ProblemCategory.PLUMBING.value,
    ProblemCategory.FURNITURE.value,
    ProblemCategory.INTERNET.value,
    ProblemCategory.OTHER.value,
    *VALID_TIMEFRAMES,
}

# --------------------------
# --- логирующие утилиты ---
# --------------------------


# функция для получения состояния пользователя 
def state_name(state: Any) -> str:
    if state is None:
        return "none"

    return getattr(state, "name", str(state))

# функция для подготовки любого значения к логированию
def to_log_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return safe_payload(value)

    if isinstance(value, list):
        return [to_log_value(item) for item in value]

    if isinstance(value, set):
        return [to_log_value(item) for item in value]

    if isinstance(value, tuple):
        return [to_log_value(item) for item in value]

    return value


# впринципе все функции ниже делают одно и тоже только для разных типов данных

# функция для скрытия чувствительной информации
def hidden_value(value: Any) -> str:
    if value is None:
        return "<none>"

    if isinstance(value, str):
        return f"<hidden length={len(value.strip())}>"

    return f"<hidden type={type(value).__name__}>"

# функция для безопасного логирования пейлоада
def safe_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not payload:
        return {}

    result: Dict[str, Any] = {}

    # пробегаемся по ключам и смотрим на данные, если ключ чувствительный - скрываем, если нет - логируем полностью
    for key, value in payload.items():
        if value is None:
            result[key] = None
            continue

        if LOG_SENSITIVE_DATA:
            result[key] = to_log_value(value)
            continue

        if key in SENSITIVE_KEYS:
            result[key] = hidden_value(value)
        else:
            result[key] = to_log_value(value)

    return result

# функция для безопасного лоигрования данных пользователя
def safe_user_data(user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not user_data:
        return {}

    if LOG_SENSITIVE_DATA:
        return safe_payload(user_data)

    return {
        "keys": sorted(list(user_data.keys())),
        "fields_count": len(user_data),
    }

# функция для безопасноого логирования текста
def safe_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None

    normalized = str(text).strip()

    if LOG_SENSITIVE_DATA:
        return normalized

    if normalized in BUTTON_TEXTS:
        return normalized

    return f"<hidden length={len(normalized)}>"

# функция для безопасного логирования тела HTTP ответа
def safe_http_body(text: str, force: bool = False) -> str:
    if force or LOG_HTTP_BODIES or LOG_SENSITIVE_DATA:
        return text

    return f"<hidden length={len(text)}>"

# функция для логирования событий с произвольными полями
def log_event(level: int, event_name: str, **fields):
    prepared_fields = {
        key: to_log_value(value)
        for key, value in fields.items()
    }

    if prepared_fields:
        logger.log(
            level,
            "%s | %s",
            event_name,
            json.dumps(prepared_fields, ensure_ascii=False, default=str),
        )
    else:
        logger.log(level, event_name)

# функция для логирования исключений с произвольными полями
def log_exception(event_name: str, **fields):
    prepared_fields = {
        key: to_log_value(value)
        for key, value in fields.items()
    }

    logger.exception(
        "%s | %s",
        event_name,
        json.dumps(prepared_fields, ensure_ascii=False, default=str),
    )


# -----------------------------
# --- основные функции бота ---
# -----------------------------

# функция для извлечения пейлоада из сообщения
def get_state_payload(message: Message) -> Dict[str, Any]:
    if not message.state_peer:
        return {}

    return message.state_peer.payload or {}

# функция для получения текущего состояния пользователя
def get_current_state_name(message: Message) -> str:
    if not message.state_peer:
        return "none"

    return state_name(message.state_peer.state)

# функция для логирования входа в обработчик с информацией о сообщении и состоянии
def log_handler_entry(handler_name: str, message: Message):
    log_event(
        logging.INFO,
        "handler_enter",
        handler=handler_name,
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        state=get_current_state_name(message),
        text=safe_text(message.text),
        payload=safe_payload(get_state_payload(message)),
    )

# функция для отправки ответа пользователю
async def send_answer(
    message: Message,
    text: str,
    keyboard: Optional[str] = None,
    event: str = "answer",
):
    log_event(
        logging.INFO,
        "outgoing_message",
        answer_event=event,
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        state=get_current_state_name(message),
        text=safe_text(text),
        keyboard_attached=keyboard is not None,
    )

    await message.answer(text, keyboard=keyboard)

# фукнция для изменения состояния у пользователя
async def set_state(
    message: Message,
    new_state: Any,
    reason: str,
    **payload,
):
    # получаем старое состояние
    old_state = get_current_state_name(message)

    log_event(
        logging.INFO,
        "state_set_started",
        reason=reason,
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        old_state=old_state,
        new_state=state_name(new_state),
        payload=safe_payload(payload),
    )

    # ставим новое состояние с пейлоадом
    await bot.state_dispenser.set(message.peer_id, new_state, **payload)

    log_event(
        logging.DEBUG,
        "state_set_finished",
        reason=reason,
        peer_id=message.peer_id,
        new_state=state_name(new_state),
    )

# функция для удаления состояния у пользователя
async def delete_state(
    message: Message,
    reason: str,
):
    # берём старое состояние и пейлоад для логирования
    old_state = get_current_state_name(message)
    old_payload = safe_payload(get_state_payload(message))

    log_event(
        logging.INFO,
        "state_delete_started",
        reason=reason,
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        old_state=old_state,
        old_payload=old_payload,
    )

    # удаляем состояние
    await bot.state_dispenser.delete(message.peer_id)

    log_event(
        logging.DEBUG,
        "state_delete_finished",
        reason=reason,
        peer_id=message.peer_id,
    )

# функция для получения вк юзер айди
def get_vk_user_id(message: Message) -> int:
    vk_user_id = int(message.from_id or message.peer_id)

    log_event(
        logging.DEBUG,
        "vk_user_id_extracted",
        peer_id=message.peer_id,
        from_id=message.from_id,
        vk_user_id=vk_user_id,
    )

    return vk_user_id

# функция для добавления аргументов к ссылке
def add_query_params(url: str, params: Dict[str, Any]) -> str:
    parsed = urlparse(url)
    current_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    current_params.update({key: str(value) for key, value in params.items()})

    result = urlunparse(parsed._replace(query=urlencode(current_params)))

    log_event(
        logging.DEBUG,
        "query_params_added",
        original_url=url,
        params=params,
        result_url=result if LOG_SENSITIVE_DATA else "<hidden url with query params>",
    )

    return result

# функция для создания ссылки на  регистрацию с вк юзер айди
def get_registration_url(vk_user_id: int) -> str:
    result = add_query_params(
        site_url(REGISTRATION_PATH),
        {"vkUserId": vk_user_id},
    )

    log_event(
        logging.INFO,
        "registration_url_created",
        vk_user_id=vk_user_id,
        registration_url=result if LOG_SENSITIVE_DATA else site_url(REGISTRATION_PATH),
    )

    return result

# функция для преобразования енум в строку для бэка
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

    if APPEAL_ENUM_FORMAT == "value":
        return value.value

    return value.name

# функция для извлечения енум из пейлоада
def enum_from_payload(enum_cls, value, default):
    if isinstance(value, enum_cls):
        log_event(
            logging.DEBUG,
            "enum_from_payload_already_enum",
            enum=enum_cls.__name__,
            value=value,
        )
        return value

    try:
        result = enum_cls(value)

        log_event(
            logging.DEBUG,
            "enum_from_payload_success",
            enum=enum_cls.__name__,
            value=value,
            result=result,
        )

        return result

    except (ValueError, TypeError):
        if value is not None:
            log_event(
                logging.WARNING,
                "enum_from_payload_failed",
                enum=enum_cls.__name__,
                value=value,
                default=default,
            )
        else:
            log_event(
                logging.DEBUG,
                "enum_from_payload_default_used_for_none",
                enum=enum_cls.__name__,
                default=default,
            )

        return default

# функция для получения категорий проблем для локации
def get_categories_for_location(location: LocationType) -> List[ProblemCategory]:
    categories = LOCATION_CATEGORIES.get(location, [ProblemCategory.OTHER])

    log_event(
        logging.DEBUG,
        "categories_for_location_resolved",
        location=location,
        categories=categories,
    )

    return categories

# функция для проверки валидности описания проблемы
def is_valid_description(text: Optional[str]) -> bool:
    result = bool(text and len(text.strip()) >= 5)

    log_event(
        logging.DEBUG,
        "description_validated",
        length=len(text.strip()) if text else 0,
        valid=result,
    )

    return result

# функция для нормализации логических значений из разных форматов
def normalize_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        log_event(
            logging.DEBUG,
            "bool_normalized",
            original_type=type(value).__name__,
            result=value,
        )
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes", "y", "да"}:
            log_event(
                logging.DEBUG,
                "bool_normalized",
                original_type=type(value).__name__,
                result=True,
            )
            return True

        if normalized in {"false", "0", "no", "n", "нет"}:
            log_event(
                logging.DEBUG,
                "bool_normalized",
                original_type=type(value).__name__,
                result=False,
            )
            return False

    log_event(
        logging.DEBUG,
        "bool_normalization_failed",
        original_type=type(value).__name__,
    )

    return None

# функция для получения первого непустого значения из словаря по списку ключей
def get_first_present(data: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = data.get(key)

        if value not in (None, ""):
            result = str(value).strip()

            log_event(
                logging.DEBUG,
                "first_present_found",
                key=key,
                value=hidden_value(result) if not LOG_SENSITIVE_DATA else result,
            )

            return result

    log_event(
        logging.DEBUG,
        "first_present_not_found",
        checked_keys=list(keys),
    )

    return None

# функция для извлечения данных пользователя из разных возможных оберток
def unwrap_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        log_event(
            logging.WARNING,
            "user_data_unwrap_failed",
            data_type=type(data).__name__,
        )
        return {}

    for key in ("userResponseDto", "user_response_dto", "user", "data", "profile"):
        value = data.get(key)

        if isinstance(value, dict):
            log_event(
                logging.DEBUG,
                "user_data_unwrapped",
                wrapper_key=key,
                user_data=safe_user_data(value),
            )
            return value

    log_event(
        logging.DEBUG,
        "user_data_used_without_unwrap",
        user_data=safe_user_data(data),
    )

    return data

# функция для скачивания файла по URL и возвращает base64-encoded строку с MIME типом
async def download_and_encode_file(url: str, filename: str) -> Optional[str]:
    try:
        # пытаемся скачать файл с помощью aiohttp и установить таймаут, чтобы не зависать на медленных ответах
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    log_event(
                        logging.WARNING,
                        "file_download_failed",
                        url=url[:100] + "..." if len(url) > 100 else url,
                        status=response.status,
                    )
                    return None
                # если скачали успешно, читаем содержимое и определяем MIME тип из заголовков
                content = await response.read()
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                
                base64_content = base64.b64encode(content).decode('utf-8')
                data_url = f"data:{content_type};base64,{base64_content}"

                log_event(
                    logging.INFO,
                    "file_downloaded_and_encoded",
                    filename=filename,
                    content_type=content_type,
                    size=len(content),
                    url=url[:100] + "..." if len(url) > 100 else url,
                )

                return data_url

    except Exception as e:
        log_event(
            logging.ERROR,
            "file_download_error",
            url=url[:100] + "..." if len(url) > 100 else url,
            filename=filename,
            error=str(e),
        )
        return None

# функция для получения флага регистрации из данных, проверяя несколько возможных ключей
def get_registration_flag_from_dict(data: Dict[str, Any]) -> Optional[bool]:
    # несколько вариантов ключей
    for key in ("exists", "registered", "isRegistered", "success"):
        if key in data:
            parsed = normalize_bool(data.get(key))

            log_event(
                logging.DEBUG,
                "registration_flag_checked",
                key=key,
                raw_value=data.get(key),
                parsed=parsed,
            )

            if parsed is not None:
                return parsed

    log_event(
        logging.DEBUG,
        "registration_flag_not_found",
        keys=list(data.keys()),
    )

    return None

# функция для построения полного имени пользователя из разных возможных полей
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
        log_event(
            logging.DEBUG,
            "full_name_resolved_from_explicit_field",
            value=hidden_value(explicit_name) if not LOG_SENSITIVE_DATA else explicit_name,
        )
        return explicit_name

    if user_data.get("middlename") or user_data.get("middleName") or user_data.get("middle_name"):
        name_parts = [
            user_data.get("lastname") or user_data.get("lastName") or user_data.get("last_name"),
            user_data.get("firstname") or user_data.get("firstName") or user_data.get("first_name"),
            user_data.get("middlename") or user_data.get("middleName") or user_data.get("middle_name"),
        ]
    else:
        name_parts = [
            user_data.get("lastname") or user_data.get("lastName") or user_data.get("last_name"),
            user_data.get("firstname") or user_data.get("firstName") or user_data.get("first_name"),
        ]

    full_name = " ".join(str(part).strip() for part in name_parts if part)

    log_event(
        logging.DEBUG,
        "full_name_built_from_parts",
        has_last_name=bool(name_parts[0]),
        has_first_name=bool(name_parts[1]),
        has_middle_name=bool(name_parts[2]),
        result=hidden_value(full_name) if full_name and not LOG_SENSITIVE_DATA else full_name,
    )

    return full_name or None

# функция для получения контакной информации
def get_user_contact_fields(user_data: Dict[str, Any]) -> Dict[str, Any]:
    user_data = unwrap_user_data(user_data)
    # проверка на согласие на обработку пд
    consent = True

    for key in (
        "personal_data_consent",
        "personalDataConsent",
        "dataProcessingConsent",
        "consent",
    ):
        if key in user_data:
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
        "contact",
        "contactLink",
        "contact_link",
        "telegram",
        "telegram_username",
        "telegramUsername",
        "vk",
        "vk_link",
        "vkLink",
    )

    result = {
        "contactName": build_full_name(user_data),
        "contactPhone": get_first_present(
            user_data,
            "contact_phone",
            "contactPhone",
            "phone",
            "phoneNumber",
            "phone_number",
        ),
        "contactEmail": contact_email,
        "personalDataConsent": consent,
    }

    log_event(
        logging.INFO,
        "user_contact_fields_resolved",
        fields=safe_payload(result),
        source_user_data=safe_user_data(user_data),
    )

    return result

# -----------
# --- api ---
# -----------

# функция для получения профиля пользователя с бэкенда
async def get_user_profile(vk_user_id: int) -> Optional[Dict[str, Any]]:
    # Берем токен из кэша
    access_token = access_tokens.get(vk_user_id)
    
    if not access_token:
        log_event(
            logging.WARNING,
            "get_user_profile_no_access_token",
            vk_user_id=vk_user_id,
        )
        return None

    url = api_url("/user/me")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    log_event(
        logging.INFO,
        "get_user_profile_started",
        vk_user_id=vk_user_id,
        url=url,
    )

    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    log_event(
                        logging.WARNING,
                        "get_user_profile_failed",
                        vk_user_id=vk_user_id,
                        status=response.status,
                        body=safe_http_body(error_text, force=LOG_ERROR_HTTP_BODIES),
                    )
                    return None
                
                payload = await read_response_payload(response)
                
                log_event(
                    logging.INFO,
                    "get_user_profile_success",
                    vk_user_id=vk_user_id,
                    data=safe_user_data(payload),
                )
                
                return payload

    except (aiohttp.ClientError, asyncio.TimeoutError):
        log_exception(
            "get_user_profile_exception",
            vk_user_id=vk_user_id,
            url=url,
        )
        return None

# функция для чтения пейлоада 
async def read_response_payload(response: aiohttp.ClientResponse) -> Any:
    text = (await response.text()).strip()

    log_event(
        logging.DEBUG,
        "api_response_body_read",
        status=response.status,
        content_type=response.headers.get("Content-Type"),
        body=safe_http_body(text),
        body_length=len(text),
    )

    if not text:
        log_event(
            logging.DEBUG,
            "api_response_body_empty",
            status=response.status,
        )
        return None

    parsed_bool = normalize_bool(text)

    if parsed_bool is not None:
        log_event(
            logging.DEBUG,
            "api_response_parsed_as_bool",
            result=parsed_bool,
        )
        return parsed_bool

    try:
        payload = json.loads(text)

        log_event(
            logging.DEBUG,
            "api_response_parsed_as_json",
            payload_type=type(payload).__name__,
            payload=safe_payload(payload) if isinstance(payload, dict) else payload,
        )

        return payload

    except json.JSONDecodeError:
        log_event(
            logging.WARNING,
            "api_response_json_parse_failed",
            body=safe_http_body(text, force=LOG_ERROR_HTTP_BODIES),
        )
        return text

# функция для парсинга пейлоада после регистрации (по сути просто проверка, что всё ок)
def parse_registration_payload(payload: Any, vk_user_id: Optional[int] = None) -> RegistrationResult:
    log_event(
        logging.DEBUG,
        "registration_payload_parse_started",
        payload_type=type(payload).__name__,
        payload=safe_payload(payload) if isinstance(payload, dict) else payload,
    )

    if isinstance(payload, bool):
        result = RegistrationResult(
            request_ok=True,
            registered=payload,
            data={},
        )

        log_event(
            logging.INFO,
            "registration_payload_parsed",
            registered=result.registered,
            data=safe_user_data(result.data),
        )

        return result

    if isinstance(payload, str):
        parsed = normalize_bool(payload)

        result = RegistrationResult(
            request_ok=True,
            registered=bool(parsed),
            data={},
        )

        log_event(
            logging.INFO,
            "registration_payload_parsed",
            registered=result.registered,
            data=safe_user_data(result.data),
        )

        return result

    if isinstance(payload, dict):
        registered = get_registration_flag_from_dict(payload)
        user_data = unwrap_user_data(payload)

        if registered is None:
            registered = bool(user_data)

        # если зареган и из вк юзер айди есть, то сохраняем токен для дальнейших запросов от имени пользователя
        if vk_user_id and registered:
            access_token = payload.get("accessToken")
            if access_token:
                access_tokens[vk_user_id] = access_token
                log_event(
                    logging.INFO,
                    "access_token_saved",
                    vk_user_id=vk_user_id,
                    token_length=len(access_token) if not LOG_SENSITIVE_DATA else len(access_token),
                )

        result = RegistrationResult(
            request_ok=True,
            registered=registered,
            data=user_data if registered else {},
        )

        log_event(
            logging.INFO,
            "registration_payload_parsed",
            registered=result.registered,
            data=safe_user_data(result.data),
        )

        return result

    result = RegistrationResult(
        request_ok=True,
        registered=False,
        data={},
    )

    log_event(
        logging.WARNING,
        "registration_payload_unknown_type",
        payload_type=type(payload).__name__,
        registered=result.registered,
    )

    return result

# функция для проверки регистрации 
async def check_user_registration(vk_user_id: int) -> RegistrationResult:
    url = api_url("/user/check")

    log_event(
        logging.INFO,
        "registration_check_started",
        vk_user_id=vk_user_id,
        url=url,
    )

    try:
        # делаем запрос к бэкенду с dr юзер айди и ждём результат. всё ок - тогда узнаём результат и топаем дальше, иначе ошибка
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.get(
                url,
                params={"vkUserId": vk_user_id},
            ) as response:
                log_event(
                    logging.INFO,
                    "registration_check_response_received",
                    vk_user_id=vk_user_id,
                    status=response.status,
                    content_type=response.headers.get("Content-Type"),
                )

                if response.status != 200:
                    error_text = await response.text()

                    log_event(
                        logging.ERROR,
                        "registration_check_bad_status",
                        vk_user_id=vk_user_id,
                        status=response.status,
                        body=safe_http_body(error_text, force=LOG_ERROR_HTTP_BODIES),
                    )

                    return RegistrationResult(
                        request_ok=False,
                        registered=False,
                        data={},
                    )

                payload = await read_response_payload(response)
                result = parse_registration_payload(payload, vk_user_id)

                log_event(
                    logging.INFO,
                    "registration_check_finished",
                    vk_user_id=vk_user_id,
                    request_ok=result.request_ok,
                    registered=result.registered,
                    user_data=safe_user_data(result.data),
                )

                return result

    except (aiohttp.ClientError, asyncio.TimeoutError):
        log_exception(
            "registration_check_exception",
            vk_user_id=vk_user_id,
            url=url,
        )

        return RegistrationResult(
            request_ok=False,
            registered=False,
            data={},
        )

# функция для отправки жалобы в бэкенд
async def send_to_backend(appeal: Appeal) -> Tuple[bool, Optional[int]]:
    url = api_url("/appeals")
    body = appeal.to_dict()

    log_event(
        logging.INFO,
        "appeal_send_started",
        url=url,
        vk_user_id=appeal.vkUserId,
        appeal_type=appeal.type,
        campusLocation=appeal.campusLocation,
        problemCategory=appeal.problemCategory,
        body=safe_payload(body),
    )
    # аццесс токен из словаря для нашего конкретного юзера
    access_token = access_tokens.get(appeal.vkUserId)
    if not access_token:
        log_event(
            logging.WARNING,
            "appeal_send_no_access_token",
            vk_user_id=appeal.vkUserId,
        )

    headers = {
        "Accept": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        # пытаемся отправить аппил на бэк
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.post(
                url,
                json=body,
                headers=headers,
            ) as response:
                response_text = await response.text()

                log_event(
                    logging.INFO,
                    "appeal_send_response_received",
                    vk_user_id=appeal.vkUserId,
                    status=response.status,
                    content_type=response.headers.get("Content-Type"),
                    body=safe_http_body(response_text),
                    body_length=len(response_text),
                )
                # если всё ок, то получаем номер жалобы и потом отправляем юзеру
                if response.status in (200, 201):
                    appeal_number = None
                    try:
                        payload = json.loads(response_text) if response_text else {}
                        if isinstance(payload, dict):
                            appeal_number = payload.get("appealNumber") or payload.get("appeal_number")
                            if appeal_number is None and isinstance(payload.get("data"), dict):
                                data_payload = payload.get("data")
                                appeal_number = data_payload.get("appealNumber") or data_payload.get("appeal_number")
                    except json.JSONDecodeError:
                        appeal_number = None

                    log_event(
                        logging.INFO,
                        "appeal_send_success",
                        vk_user_id=appeal.vkUserId,
                        status=response.status,
                        appeal_number=appeal_number,
                    )
                    return True, appeal_number

                log_event(
                    logging.ERROR,
                    "appeal_send_bad_status",
                    vk_user_id=appeal.vkUserId,
                    status=response.status,
                    request_body=safe_payload(body),
                    response_body=safe_http_body(response_text, force=LOG_ERROR_HTTP_BODIES),
                )

                return False, None

    except (aiohttp.ClientError, asyncio.TimeoutError):
        log_exception(
            "appeal_send_exception",
            vk_user_id=appeal.vkUserId,
            url=url,
            request_body=safe_payload(body),
        )
        return False, None

# функция для сохранения жалобы в бд через бэкенд
async def save_appeal_to_db(appeal: Appeal) -> Tuple[bool, Optional[int]]:
    log_event(
        logging.INFO,
        "appeal_save_started",
        vk_user_id=appeal.vkUserId,
        appeal_type=appeal.type,
    )

    result, appeal_number = await send_to_backend(appeal)

    log_event(
        logging.INFO if result else logging.ERROR,
        "appeal_save_finished",
        vk_user_id=appeal.vkUserId,
        success=result,
        appeal_number=appeal_number,
    )

    return result, appeal_number

# функция для построения объекта жалобы из пейлоада и данных профиля
async def build_appeal_from_payload(
    payload: Dict[str, Any],
    vk_user_id: int,
) -> Tuple[Optional[Appeal], RegistrationResult]:
    log_event(
        logging.INFO,
        "appeal_build_started",
        vk_user_id=vk_user_id,
        payload=safe_payload(payload),
    )
    # проверяем регистрацию юзера
    registration = await check_user_registration(vk_user_id)

    if not registration.request_ok or not registration.registered:
        log_event(
            logging.WARNING,
            "appeal_build_stopped_registration_failed",
            vk_user_id=vk_user_id,
            request_ok=registration.request_ok,
            registered=registration.registered,
        )
        return None, registration

    # получаем профиль пользователя по токену
    user_profile_data = await get_user_profile(vk_user_id)
    
    # если профиль получить не удалось, подстраховываемся данными из регистрации
    contact_source_data = user_profile_data if user_profile_data else registration.data

    # получаем контактные данные из профиля
    user_fields = get_user_contact_fields(contact_source_data)

    # тут потихоньку всё собирается 
    appeal_type = enum_from_payload(
        AppealType,
        payload.get("type"),
        AppealType.SUGGESTION,
    )

    campusLocation = enum_from_payload(
        LocationType,
        payload.get("campusLocation"),
        None,
    )

    problemCategory = enum_from_payload(
        ProblemCategory,
        payload.get("problemCategory"),
        None,
    )

    timeframe = enum_from_payload(
        Timeframe,
        payload.get("timeframe"),
        None,
    )
    
    # у предложения, запроса и вопроса нет локации и категории проблемы
    if appeal_type != AppealType.COMPLAINT:
        if campusLocation is None:
            campusLocation = LocationType.STUDENT_CAMPUS

        if problemCategory is None:
            problemCategory = ProblemCategory.OTHER

    appeal = Appeal(
        type=appeal_type,
        description=str(payload.get("description", "")).strip(),
        personalDataConsent=user_fields.get("personalDataConsent", True),
        vkUserId=vk_user_id,
        campusLocation=campusLocation,
        problemCategory=problemCategory,
        timeframe=timeframe,
        attachments=payload.get("attachments", []),
        contactName=user_fields.get("contactName"),
        contactPhone=user_fields.get("contactPhone"),
        contactEmail=user_fields.get("contactEmail"),
    )

    log_event(
        logging.INFO,
        "appeal_build_finished",
        vk_user_id=vk_user_id,
        appeal_type=appeal.type,
        campusLocation=appeal.campusLocation,
        problemCategory=appeal.problemCategory,
        contact_fields=safe_payload(user_fields),
    )

    return appeal, registration

# ------------------
# --- клавиатуры ---
# ------------------

# клавиатура для проверки регистрации (после приветственного сообщения)
def get_registration_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="registration")

    return (
        Keyboard(one_time=False)
        .add(Text(CHECK_REGISTRATION_BUTTON), color=KeyboardButtonColor.POSITIVE)
        .get_json()
    )

# клавиатура для начального меню
def get_start_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="start")

    return (
        Keyboard(one_time=False)
        .add(Text(START_BUTTON), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text(CHECK_REGISTRATION_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

# клавиатура для выбора типа обращения
def get_type_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="type")

    return (
        Keyboard(one_time=True)
        .add(Text(AppealType.COMPLAINT.value), color=KeyboardButtonColor.NEGATIVE)
        .add(Text(AppealType.SUGGESTION.value), color=KeyboardButtonColor.POSITIVE)
        .row()
        .add(Text(AppealType.QUESTION.value), color=KeyboardButtonColor.PRIMARY)
        .add(Text(AppealType.REQUEST.value), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text(CANCEL_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

# клавиатура для навигации назад и отмены
def get_navigation_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="navigation")

    return (
        Keyboard(one_time=True)
        .add(Text(BACK_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .add(Text(CANCEL_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

# функция для добавления навигационных кнопок к существующей клавиатуре
def add_navigation(kb: Keyboard) -> Keyboard:
    log_event(logging.DEBUG, "keyboard_navigation_added")

    kb.row()
    kb.add(Text(BACK_BUTTON), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text(CANCEL_BUTTON), color=KeyboardButtonColor.SECONDARY)

    return kb

# клавиатура для выбора локации
def get_location_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="location")

    kb = Keyboard(one_time=True)

    locations = [
        LocationType.STUDENT_CAMPUS,
        LocationType.DORMITORY,
        LocationType.ACADEMIC_BUILDING,
        LocationType.LIBRARY,
        LocationType.CANTEEN,
        LocationType.SPORTS_COMPLEX,
        LocationType.MEDICAL_CENTER,
    ]

    for index, location in enumerate(locations):
        if index > 0 and index % 2 == 0:
            kb.row()

        kb.add(Text(location.value), color=KeyboardButtonColor.PRIMARY)

    return add_navigation(kb).get_json()

# клавиатура для выбора категории проблемы, зависит от ранее выбранной локации
def get_category_kb(location: LocationType):
    categories = get_categories_for_location(location)

    log_event(
        logging.DEBUG,
        "keyboard_created",
        keyboard="category",
        location=location,
        categories=categories,
    )

    kb = Keyboard(one_time=True)

    for index, category in enumerate(categories):
        if index > 0 and index % 2 == 0:
            kb.row()

        kb.add(Text(category.value), color=KeyboardButtonColor.SECONDARY)

    return add_navigation(kb).get_json()

# клавиатура для выбора временного интервала, зависит от типа обращения (для жалобы показывается, для остальных нет)
def get_timeframe_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="timeframe")

    kb = Keyboard(one_time=True)

    timeframes = [
        Timeframe.ONE_DAY,
        Timeframe.TWO_DAYS,
        Timeframe.THREE_DAYS,
        Timeframe.FIVE_DAYS,
        Timeframe.ONE_WEEK,
        Timeframe.TWO_WEEKS,
        Timeframe.ONE_MONTH,
    ]

    for index, timeframe in enumerate(timeframes):
        if index > 0 and index % 2 == 0:
            kb.row()

        kb.add(Text(timeframe.value), color=KeyboardButtonColor.PRIMARY if index < 3 else KeyboardButtonColor.SECONDARY)

    return add_navigation(kb).get_json()

# клавиатура для управления добавлением файлов
def get_files_kb():
    log_event(logging.DEBUG, "keyboard_created", keyboard="files")

    return (
        Keyboard(one_time=False)
        .add(Text("Пропустить"), color=KeyboardButtonColor.SECONDARY)
        .add(Text(BACK_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

# -------------------
# --- регистрация ---
# -------------------

# кеш для хранения информации о верифицированных пользователях
verified_users: set[int] = set() # множество проверенных пользователей
registration_intro_sent_users: set[int] = set() # множество юзеров, которым отправуили приветственное сообщение
registration_check_locks: Dict[int, asyncio.Lock] = {} # словарь локов для каждого юзера, чтобы избежать гонок при одновременной проверке регистрации
processed_registration_check_messages: set[tuple] = set() # множество обработанных сообщений при проверке регистрации
processed_registration_check_message_order: List[tuple] = [] # порядок обработки сообщений при проверке регистрации
PROCESSED_REGISTRATION_CHECK_LIMIT = 1000

# Хранилище access tokens для каждого пользователя
access_tokens: Dict[int, str] = {}

# функция для получения асинхронного локера для конкретного пользователя, чтобы избежать гонок (одновременных обращений к бд) при одновременной проверке регистрации
def get_registration_check_lock(vk_user_id: int) -> asyncio.Lock:
    if vk_user_id not in registration_check_locks:
        registration_check_locks[vk_user_id] = asyncio.Lock()

    return registration_check_locks[vk_user_id]

# функция для генерации ключа для дедупликации сообщений при проверке регистрации, чтобы избежать повторной обработки одного и того же сообщения из-за нескольких событий или обновлений
def get_message_dedup_key(message: Message) -> tuple:
    return (
        message.peer_id,
        getattr(message, "conversation_message_id", None),
        getattr(message, "id", None),
        getattr(message, "date", None),
        (message.text or "").strip(),
    )

# функция для отметки сообщения как обработанного при проверке регистрации и проверки на дубликаты, чтобы избежать повторной обработки одного и того же сообщения
def mark_registration_check_message(message: Message) -> bool:
    key = get_message_dedup_key(message)
    # если ключ уже есть в множестве обработанных сообщений, то это дубликат и мы пропускаем его, иначе добавляем в множество и продолжаем обработку. 
    # Также поддерживаем порядок обработки сообщений, чтобы не превышать лимит и не держать слишком много ключей в памяти. 
    if key in processed_registration_check_messages:
        log_event(
            logging.WARNING,
            "registration_check_duplicate_message_skipped",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            message_key=key,
        )
        return False

    processed_registration_check_messages.add(key)
    processed_registration_check_message_order.append(key)
    # если количество обработанных сообщений превышает лимит, то удаляем самые старые ключи из множества и порядка, чтобы не держать слишком много данных в памяти
    while len(processed_registration_check_message_order) > PROCESSED_REGISTRATION_CHECK_LIMIT:
        old_key = processed_registration_check_message_order.pop(0)
        processed_registration_check_messages.discard(old_key)

    log_event(
        logging.DEBUG,
        "registration_check_message_marked",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        processed_count=len(processed_registration_check_messages),
    )

    return True


log_event(
    logging.INFO,
    "runtime_caches_initialized",
    verified_users_count=len(verified_users),
    registration_intro_sent_users_count=len(registration_intro_sent_users),
)

# функции для отправки различных сообщений, связанных с регистрацией, и для управления потоком регистрации и началом процесса подачи жалобы
async def send_registration_intro(message: Message):
    vk_user_id = get_vk_user_id(message)
    registration_intro_sent_users.add(vk_user_id)

    registration_url = get_registration_url(vk_user_id)

    log_event(
        logging.INFO,
        "registration_intro_sending",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
        intro_sent_users_count=len(registration_intro_sent_users),
        registration_url=registration_url if LOG_SENSITIVE_DATA else site_url(REGISTRATION_PATH),
    )

    text = (
        "Добро пожаловать в модуль «Предложалоба».\n\n"
        "Перед отправкой обращения нужно зарегистрироваться на сайте.\n\n"
        f"Ссылка на регистрацию:\n{registration_url}\n\n"
        f"Если вы уже зарегистрированы на сайте, то привяжите свою учетную запись к VK по следующей ссылке:\n{"<<ЗАГЛУШКА>>"}\n\n" 
        "После регистрации нажмите «Проверить регистрацию»."
        )   
    # TODO: прикрутить реальную ссылку для привязки учетной записи после реализации этого функционала на бэкенде
    await send_answer(
        message,
        text,
        keyboard=get_registration_kb(),
        event="registration_intro",
    )

# функция для отправки сообщения о необходимости регистрации, если пользователь не зарегистрирован
async def send_registration_required(message: Message):
    vk_user_id = get_vk_user_id(message)
    registration_url = get_registration_url(vk_user_id)

    log_event(
        logging.INFO,
        "registration_required_sending",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
        registration_url=registration_url if LOG_SENSITIVE_DATA else site_url(REGISTRATION_PATH),
    )

    text = (
        "Регистрация не найдена.\n\n"
        "Перед отправкой обращения нужно зарегистрироваться на сайте.\n\n"
        f"Ссылка на регистрацию:\n{registration_url}\n\n"
        f"Если вы уже зарегистрированы на сайте, то привяжите свою учетную запись к VK по следующей ссылке:\n{"<<ЗАГЛУШКА>>"}\n\n" 
        "После регистрации нажмите «Проверить регистрацию»."
    )

    await send_answer(
        message,
        text,
        keyboard=get_registration_kb(),
        event="registration_required",
    )

# функция для отправки сообщения об ошибке при проверке регистрации
async def send_registration_error(message: Message):
    log_event(
        logging.ERROR,
        "registration_error_message_sending",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
    )

    await send_answer(
        message,
        "Возникла ошибка при проверке регистрации. Попробуйте позже.",
        keyboard=get_registration_kb(),
        event="registration_error",
    )

# функция для проверки регистрации пользователя и управления потоком в зависимости от результата, 
# включая отправку соответствующих сообщений и начало процесса подачи жалобы, если регистрация подтверждена
async def require_registered(message: Message) -> Optional[RegistrationResult]:
    vk_user_id = get_vk_user_id(message)

    log_event(
        logging.INFO,
        "require_registered_started",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
    )

    result = await check_user_registration(vk_user_id)
    # если ошибка 
    if not result.request_ok:
        log_event(
            logging.ERROR,
            "require_registered_failed_request_error",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
        )

        await send_registration_error(message)
        return None
    # если не зареган
    if not result.registered:
        verified_users.discard(vk_user_id)

        log_event(
            logging.INFO,
            "require_registered_failed_not_registered",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            verified_users_count=len(verified_users),
        )

        await send_registration_required(message)
        return None
    #  если зареган
    verified_users.add(vk_user_id)

    log_event(
        logging.INFO,
        "require_registered_success",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
        verified_users_count=len(verified_users),
    )

    return result

# функция для начала потока подачи жалобы после подтверждения регистрации
async def start_appeal_flow(message: Message):
    log_event(
        logging.INFO,
        "appeal_flow_starting",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
    )
    # ставим состояние ожидания типа
    await set_state(
        message,
        AppealState.WAITING_FOR_TYPE,
        reason="start_appeal_flow",
    )

    await send_answer(
        message,
        "Регистрация подтверждена.\nВыберите тип обращения:",
        keyboard=get_type_kb(),
        event="appeal_flow_started",
    )

# функция для обработки нажатия кнопки проверки регистрации, включая дедупликацию сообщений, 
# управление асинхронным доступом к проверке регистрации для одного пользователя и отправку соответствующих сообщений в зависимости от результата проверки
async def process_registration_check(message: Message) -> bool:
    vk_user_id = get_vk_user_id(message)

    log_event(
        logging.INFO,
        "registration_check_button_processing_started",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
        state=get_current_state_name(message),
    )

    if not mark_registration_check_message(message):
        return True

    lock = get_registration_check_lock(vk_user_id)

    async with lock:
        current_state = message.state_peer.state if message.state_peer else None

        if vk_user_id in verified_users:
            log_event(
                logging.INFO,
                "registration_check_user_already_verified",
                peer_id=message.peer_id,
                vk_user_id=vk_user_id,
                state=get_current_state_name(message),
            )

            if message.state_peer:
                if current_state == AppealState.WAITING_FOR_TYPE:
                    await send_answer(
                        message,
                        "Регистрация уже подтверждена. Выберите тип обращения:",
                        keyboard=get_type_kb(),
                        event="registration_already_confirmed_type_state",
                    )
                else:
                    await send_answer(
                        message,
                        "Регистрация уже подтверждена. Продолжайте текущий шаг или нажмите «Отмена».",
                        keyboard=get_navigation_kb(),
                        event="registration_already_confirmed_active_state",
                    )

                return True

            await start_appeal_flow(message)
            return True

        result = await check_user_registration(vk_user_id)

        if not result.request_ok:
            log_event(
                logging.ERROR,
                "registration_check_button_processing_failed_request_error",
                peer_id=message.peer_id,
                vk_user_id=vk_user_id,
            )

            await send_registration_error(message)
            return False

        if not result.registered:
            verified_users.discard(vk_user_id)

            log_event(
                logging.INFO,
                "registration_check_button_processing_not_registered",
                peer_id=message.peer_id,
                vk_user_id=vk_user_id,
                verified_users_count=len(verified_users),
            )

            await send_registration_required(message)
            return False

        verified_users.add(vk_user_id)

        log_event(
            logging.INFO,
            "registration_check_button_processing_success",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            verified_users_count=len(verified_users),
            state=get_current_state_name(message),
        )

        if message.state_peer:
            current_state = message.state_peer.state

            if current_state == AppealState.WAITING_FOR_TYPE:
                await send_answer(
                    message,
                    "Регистрация подтверждена. Выберите тип обращения:",
                    keyboard=get_type_kb(),
                    event="registration_confirmed_in_type_state",
                )
                return True

            await send_answer(
                message,
                "Регистрация подтверждена. Продолжайте текущий шаг или нажмите «Отмена».",
                keyboard=get_navigation_kb(),
                event="registration_confirmed_in_active_state",
            )
            return True

        await start_appeal_flow(message)
        return True

# -----------------
# --- навигация ---
# -----------------

# декоратор для обработки навигационных кнопок "Назад" и "Отмена" в любом месте потока подачи жалобы
def handle_navigation(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        text = (message.text or "").strip()

        log_event(
            logging.DEBUG,
            "navigation_wrapper_enter",
            handler=func.__name__,
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            state=get_current_state_name(message),
            text=safe_text(text),
        )

        if text == CANCEL_BUTTON:
            log_event(
                logging.INFO,
                "navigation_cancel_received",
                handler=func.__name__,
                peer_id=message.peer_id,
                vk_user_id=get_vk_user_id(message),
            )

            await delete_state(message, reason="user_cancel")
            await send_answer(
                message,
                "Действие отменено. Нажмите «Начать», чтобы начать заново.",
                keyboard=get_start_kb(),
                event="cancelled",
            )
            return

        if text == BACK_BUTTON:
            log_event(
                logging.INFO,
                "navigation_back_received",
                handler=func.__name__,
                peer_id=message.peer_id,
                vk_user_id=get_vk_user_id(message),
            )

            await back_action(message)
            return

        if text == CHECK_REGISTRATION_BUTTON:
            log_event(
                logging.INFO,
                "navigation_registration_check_received",
                handler=func.__name__,
                peer_id=message.peer_id,
                vk_user_id=get_vk_user_id(message),
            )

            await process_registration_check(message)
            return

        await func(message, *args, **kwargs)

    return wrapper

# функция для обработки нажатия кнопки "Назад" в зависимости от текущего состояния потока подачи жалобы
async def back_action(message: Message):
    log_handler_entry("back_action", message)

    if not message.state_peer:
        log_event(
            logging.WARNING,
            "back_action_without_state",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )
        return

    current_state = message.state_peer.state
    payload = message.state_peer.payload or {}
    appeal_type = enum_from_payload(AppealType, payload.get("type"), None)

    log_event(
        logging.INFO,
        "back_action_processing",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        current_state=state_name(current_state),
        payload=safe_payload(payload),
        appeal_type=appeal_type,
    )

    if current_state == AppealState.WAITING_FOR_LOCATION:
        await set_state(
            message,
            AppealState.WAITING_FOR_TYPE,
            reason="back_from_location",
        )
        await send_answer(
            message,
            "Выберите тип обращения:",
            keyboard=get_type_kb(),
            event="back_to_type",
        )
        return

    if current_state == AppealState.WAITING_FOR_CATEGORY:
        await set_state(
            message,
            AppealState.WAITING_FOR_LOCATION,
            reason="back_from_category",
            **payload,
        )
        await send_answer(
            message,
            "Выберите локацию проблемы:",
            keyboard=get_location_kb(),
            event="back_to_location",
        )
        return

    if current_state == AppealState.WAITING_FOR_TIMEFRAME:
        location = enum_from_payload(
            LocationType,
            payload.get("campusLocation"),
            None,
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_CATEGORY,
            reason="back_from_timeframe",
            **payload,
        )
        await send_answer(
            message,
            "Выберите категорию проблемы:",
            keyboard=get_category_kb(location),
            event="back_to_category",
        )
        return

    if current_state == AppealState.WAITING_FOR_DESCRIPTION:
        if appeal_type == AppealType.COMPLAINT:
            await set_state(
                message,
                AppealState.WAITING_FOR_TIMEFRAME,
                reason="back_from_description_to_timeframe",
                **payload,
            )
            await send_answer(
                message,
                "Укажите ориентировочные сроки:",
                keyboard=get_timeframe_kb(),
                event="back_to_timeframe",
            )
        else:
            await set_state(
                message,
                AppealState.WAITING_FOR_TYPE,
                reason="back_from_description_to_type",
                **payload,
            )
            await send_answer(
                message,
                "Выберите тип обращения:",
                keyboard=get_type_kb(),
                event="back_to_type",
            )
        return

    if current_state == AppealState.WAITING_FOR_FILES:
        await set_state(
            message,
            AppealState.WAITING_FOR_DESCRIPTION,
            reason="back_from_files_to_description",
            **payload,
        )
        await send_answer(
            message,
            "Опишите обращение подробнее:",
            keyboard=get_navigation_kb(),
            event="back_to_description_from_files",
        )
        return

    log_event(
        logging.WARNING,
        "back_action_unknown_state",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        current_state=state_name(current_state),
    )

    await set_state(
        message,
        AppealState.WAITING_FOR_TYPE,
        reason="back_unknown_state_to_type",
    )
    await send_answer(
        message,
        "Выберите тип обращения:",
        keyboard=get_type_kb(),
        event="back_to_type_fallback",
    )

# -------------------
# --- обработчики ---
# -------------------
# впринципе у обработчиков простая логика и она видна по коду, потому не буду её расписывать
# единственное что - локация, категория и время только для жалобы, всё остальное только тип и описание

# обработчик для кнопки проверки регистрации
@bot.on.message(text=[CHECK_REGISTRATION_BUTTON])
async def check_registration_handler(message: Message):
    log_handler_entry("check_registration_handler", message)
    await process_registration_check(message)

# обработчик для начального сообщения
@bot.on.message(text=[START_BUTTON, "Привет", "предложалоба", "Предложалоба"])
async def start_handler(message: Message):
    log_handler_entry("start_handler", message)

    if message.state_peer:
        log_event(
            logging.INFO,
            "start_handler_blocked_by_active_state",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            state=get_current_state_name(message),
        )

        await send_answer(
            message,
            "Сначала завершите текущее обращение или нажмите «Отмена».",
            keyboard=get_navigation_kb(),
            event="start_blocked_by_state",
        )
        return

    vk_user_id = get_vk_user_id(message)

    if vk_user_id not in registration_intro_sent_users and vk_user_id not in verified_users:
        log_event(
            logging.INFO,
            "start_handler_first_contact",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
        )

        await send_registration_intro(message)
        return

    if vk_user_id in verified_users:
        log_event(
            logging.INFO,
            "start_handler_user_already_verified",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
        )

        await start_appeal_flow(message)
        return

    log_event(
        logging.INFO,
        "start_handler_intro_already_sent_not_verified",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
    )

    await send_registration_intro(message)

# обработчик для выбора типа обращения
@bot.on.message(state=AppealState.WAITING_FOR_TYPE)
async def type_handler(message: Message):
    log_handler_entry("type_handler", message)

    text = (message.text or "").strip()
    normalized_text = text.lower()

    if normalized_text == CANCEL_BUTTON.lower():
        log_event(
            logging.INFO,
            "type_handler_cancel",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await delete_state(message, reason="type_handler_cancel")
        await send_answer(
            message,
            "Действие отменено. Нажмите «Начать», чтобы начать заново.",
            keyboard=get_start_kb(),
            event="type_cancelled",
        )
        return

    if normalized_text == BACK_BUTTON.lower():
        log_event(
            logging.INFO,
            "type_handler_back_on_first_step",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await send_answer(
            message,
            "Вы уже на первом шаге.",
            keyboard=get_type_kb(),
            event="back_on_first_step",
        )
        return

    if normalized_text == CHECK_REGISTRATION_BUTTON.lower():
        log_event(
            logging.INFO,
            "type_handler_registration_check",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await process_registration_check(message)
        return

    if get_vk_user_id(message) not in verified_users:
        log_event(
            logging.WARNING,
            "type_handler_unverified_user",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await send_registration_intro(message)
        return

    if normalized_text == AppealType.COMPLAINT.value.lower():
        log_event(
            logging.INFO,
            "type_handler_complaint_selected",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_LOCATION,
            reason="complaint_selected",
            type=AppealType.COMPLAINT.value,
        )
        await send_answer(
            message,
            "Выберите локацию проблемы:",
            keyboard=get_location_kb(),
            event="complaint_location_requested",
        )
        return

    if normalized_text == AppealType.SUGGESTION.value.lower():
        log_event(
            logging.INFO,
            "type_handler_suggestion_selected",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_DESCRIPTION,
            reason="suggestion_selected",
            type=AppealType.SUGGESTION.value,
        )
        await send_answer(
            message,
            "Опишите суть вашего предложения:",
            keyboard=get_navigation_kb(),
            event="suggestion_description_requested",
        )
        return

    if normalized_text == AppealType.QUESTION.value.lower():
        log_event(
            logging.INFO,
            "type_handler_question_selected",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_DESCRIPTION,
            reason="question_selected",
            type=AppealType.QUESTION.value,
        )
        await send_answer(
            message,
            "Опишите суть вашего вопроса:",
            keyboard=get_navigation_kb(),
            event="question_description_requested",
        )
        return

    if normalized_text == AppealType.REQUEST.value.lower():
        log_event(
            logging.INFO,
            "type_handler_request_selected",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_DESCRIPTION,
            reason="request_selected",
            type=AppealType.REQUEST.value,
        )
        await send_answer(
            message,
            "Опишите суть вашего запроса:",
            keyboard=get_navigation_kb(),
            event="request_description_requested",
        )
        return

    log_event(
        logging.WARNING,
        "type_handler_invalid_input",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        text=safe_text(text),
    )

    await send_answer(
        message,
        "Пожалуйста, воспользуйтесь кнопками.",
        keyboard=get_type_kb(),
        event="type_invalid_input",
    )

# обработчик для локации
@bot.on.message(state=AppealState.WAITING_FOR_LOCATION)
@handle_navigation
async def location_handler(message: Message):
    log_handler_entry("location_handler", message)

    text = (message.text or "").strip()

    try:
        location = LocationType(text)

        log_event(
            logging.INFO,
            "location_handler_location_selected",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            location=location,
        )

    except ValueError:
        log_event(
            logging.WARNING,
            "location_handler_invalid_location",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            text=safe_text(text),
        )

        await send_answer(
            message,
            "Выберите локацию из списка.",
            keyboard=get_location_kb(),
            event="location_invalid_input",
        )
        return

    payload = (message.state_peer.payload or {}).copy()
    payload["campusLocation"] = location.value

    await set_state(
        message,
        AppealState.WAITING_FOR_CATEGORY,
        reason="location_selected",
        **payload,
    )

    await send_answer(
        message,
        "Выберите категорию проблемы:",
        keyboard=get_category_kb(location),
        event="category_requested",
    )

# обработчик для категории
@bot.on.message(state=AppealState.WAITING_FOR_CATEGORY)
@handle_navigation
async def category_handler(message: Message):
    log_handler_entry("category_handler", message)

    text = (message.text or "").strip()
    payload = (message.state_peer.payload or {}).copy()

    location = enum_from_payload(
        LocationType,
        payload.get("campusLocation"),
        None,
    )

    appeal_type = enum_from_payload(
        AppealType,
        payload.get("type"),
        None,
    )

    allowed_categories = get_categories_for_location(location)

    try:
        category = ProblemCategory(text)

        log_event(
            logging.INFO,
            "category_handler_category_selected",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            location=location,
            category=category,
        )

    except ValueError:
        log_event(
            logging.WARNING,
            "category_handler_invalid_category",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            location=location,
            text=safe_text(text),
        )

        await send_answer(
            message,
            "Выберите категорию из списка.",
            keyboard=get_category_kb(location),
            event="category_invalid_input",
        )
        return

    if category not in allowed_categories:
        log_event(
            logging.WARNING,
            "category_handler_category_not_allowed_for_location",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            location=location,
            category=category,
            allowed_categories=allowed_categories,
        )

        await send_answer(
            message,
            "Эта категория недоступна для выбранной локации.",
            keyboard=get_category_kb(location),
            event="category_not_allowed",
        )
        return

    payload["problemCategory"] = category.value

    if appeal_type == AppealType.COMPLAINT:
        await set_state(
            message,
            AppealState.WAITING_FOR_TIMEFRAME,
            reason="category_selected",
            **payload,
        )

        await send_answer(
            message,
            "Укажите ориентировочные сроки:",
            keyboard=get_timeframe_kb(),
            event="timeframe_requested",
        )
        return

    await set_state(
        message,
        AppealState.WAITING_FOR_DESCRIPTION,
        reason="category_selected",
        **payload,
    )

    description_prompt = {
        AppealType.SUGGESTION: "Опишите суть вашего предложения:",
        AppealType.QUESTION: "Опишите суть вашего вопроса:",
        AppealType.REQUEST: "Опишите суть вашего запроса:",
    }.get(appeal_type, "Опишите суть обращения:")

    await send_answer(
        message,
        description_prompt,
        keyboard=get_navigation_kb(),
        event="description_requested",
    )

# обработчик для сроков
@bot.on.message(state=AppealState.WAITING_FOR_TIMEFRAME)
@handle_navigation
async def timeframe_handler(message: Message):
    log_handler_entry("timeframe_handler", message)

    text = (message.text or "").strip()

    if text not in VALID_TIMEFRAMES:
        log_event(
            logging.WARNING,
            "timeframe_handler_invalid_timeframe",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            text=safe_text(text),
            valid_timeframes=VALID_TIMEFRAMES,
        )

        await send_answer(
            message,
            "Пожалуйста, воспользуйтесь кнопками.",
            keyboard=get_timeframe_kb(),
            event="timeframe_invalid_input",
        )
        return

    log_event(
        logging.INFO,
        "timeframe_handler_timeframe_selected",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        timeframe=text,
    )

    payload = (message.state_peer.payload or {}).copy()
    payload["timeframe"] = text

    await set_state(
        message,
        AppealState.WAITING_FOR_DESCRIPTION,
        reason="timeframe_selected",
        **payload,
    )

    await send_answer(
        message,
        "Опишите суть вашей проблемы подробно:",
        keyboard=get_navigation_kb(),
        event="description_requested",
    )

# обработчик для описания
@bot.on.message(state=AppealState.WAITING_FOR_DESCRIPTION)
@handle_navigation
async def description_handler(message: Message):
    log_handler_entry("description_handler", message)

    text = (message.text or "").strip()

    if not is_valid_description(text):
        log_event(
            logging.WARNING,
            "description_handler_invalid_description",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            description_length=len(text),
        )

        await send_answer(
            message,
            "Описание слишком короткое. Опишите обращение подробнее:",
            keyboard=get_navigation_kb(),
            event="description_too_short",
        )
        return

    payload = (message.state_peer.payload or {}).copy()
    payload["description"] = text

    log_event(
        logging.INFO,
        "description_handler_description_received",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
        payload=safe_payload(payload),
    )

    vk_user_id = get_vk_user_id(message)
    appeal, registration = await build_appeal_from_payload(payload, vk_user_id)

    if not registration.request_ok:
        log_event(
            logging.ERROR,
            "description_handler_registration_check_error",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
        )

        await send_answer(
            message,
            "Возникла ошибка при проверке регистрации. Попробуйте позже.",
            keyboard=get_navigation_kb(),
            event="final_registration_check_error",
        )
        return

    if not registration.registered:
        verified_users.discard(vk_user_id)

        log_event(
            logging.INFO,
            "description_handler_user_not_registered_on_final_check",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            verified_users_count=len(verified_users),
        )

        await delete_state(message, reason="final_registration_check_not_registered")
        await send_registration_required(message)
        return

    if appeal is None:
        log_event(
            logging.ERROR,
            "description_handler_appeal_none_after_build",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            payload=safe_payload(payload),
        )

        await delete_state(message, reason="appeal_build_failed")
        await send_answer(
            message,
            "Возникла ошибка при формировании обращения. Попробуйте позже.",
            keyboard=get_start_kb(),
            event="appeal_build_error",
        )
        return

    await set_state(
        message,
        AppealState.WAITING_FOR_FILES,
        reason="description_received_moving_to_files",
        **payload,
    )

    log_event(
        logging.INFO,
        "description_handler_moving_to_files",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
    )

    await send_answer(
        message,
        "📎 Если у вас есть файлы (JPG, PNG, PDF), которые помогут описать проблему, отправьте их.\n\nИли нажмите 'Пропустить', чтобы отправить обращение без файлов:",
        keyboard=get_files_kb(),
        event="files_step_started",
    )

# обработчик для файлов
@bot.on.message(state=AppealState.WAITING_FOR_FILES)
@handle_navigation
async def files_handler(message: Message):
    log_handler_entry("files_handler", message)

    text = (message.text or "").strip()

    payload = (message.state_peer.payload or {}).copy()

    if text == "Пропустить":
        log_event(
            logging.INFO,
            "files_handler_skip_files",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await finalize_appeal(message, payload)
        return

    if text == BACK_BUTTON:
        log_event(
            logging.INFO,
            "files_handler_back_to_description",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_DESCRIPTION,
            reason="files_back_to_description",
            **payload,
        )

        await send_answer(
            message,
            "Опишите обращение подробнее:",
            keyboard=get_navigation_kb(),
            event="back_to_description_from_files",
        )
        return

    attachments = payload.get("attachments", [])
    new_attachments = []

    message_attachments = getattr(message, "attachments", None) or []
    if isinstance(message_attachments, dict):
        message_attachments = [message_attachments]

    def normalize_list(item):
        return item if isinstance(item, list) else [item] if item is not None else []

    for attachment in normalize_list(message_attachments):
        att_type = None
        if isinstance(attachment, dict):
            att_type = attachment.get("type")
        else:
            att_type = getattr(attachment, "type", None)

        if att_type == "photo" or getattr(attachment, "photo", None) is not None:
            photo = attachment["photo"] if isinstance(attachment, dict) else attachment.photo
            try:
                photo_url = None
                sizes = photo.get("sizes") if isinstance(photo, dict) else getattr(photo, "sizes", None)
                if sizes:
                    sorted_sizes = sorted(
                        sizes,
                        key=lambda s: ((s.get("width", 0) * s.get("height", 0)) if isinstance(s, dict) else (getattr(s, "width", 0) * getattr(s, "height", 0))),
                        reverse=True,
                    )
                    best = sorted_sizes[0]
                    photo_url = best.get("url") if isinstance(best, dict) else getattr(best, "url", None)

                if not photo_url:
                    photo_url = photo.get("url") if isinstance(photo, dict) else getattr(photo, "url", None)

                if photo_url:
                    base64_data = await download_and_encode_file(
                        photo_url,
                        f"photo_{len(attachments) + len(new_attachments) + 1}.jpg",
                    )
                    if base64_data:
                        new_attachments.append(base64_data)
                        log_event(
                            logging.INFO,
                            "files_handler_photo_added",
                            peer_id=message.peer_id,
                            vk_user_id=get_vk_user_id(message),
                            photo_url=photo_url[:100] + "..." if len(photo_url) > 100 else photo_url,
                        )
            except Exception as e:
                log_event(
                    logging.ERROR,
                    "files_handler_photo_processing_error",
                    peer_id=message.peer_id,
                    vk_user_id=get_vk_user_id(message),
                    error=str(e),
                )

        elif att_type == "doc" or getattr(attachment, "doc", None) is not None:
            doc = attachment["doc"] if isinstance(attachment, dict) else attachment.doc
            try:
                if isinstance(doc, dict):
                    doc_url = doc.get("url")
                    doc_title = doc.get("title") or doc.get("filename")
                else:
                    doc_url = getattr(doc, "url", None)
                    doc_title = getattr(doc, "title", None) or getattr(doc, "filename", None)

                if doc_url:
                    base64_data = await download_and_encode_file(
                        doc_url,
                        doc_title or f"document_{len(attachments) + len(new_attachments) + 1}",
                    )
                    if base64_data:
                        new_attachments.append(base64_data)
                        log_event(
                            logging.INFO,
                            "files_handler_document_added",
                            peer_id=message.peer_id,
                            vk_user_id=get_vk_user_id(message),
                            doc_title=doc_title,
                            doc_url=doc_url[:100] + "..." if len(doc_url) > 100 else doc_url,
                        )
            except Exception as e:
                log_event(
                    logging.ERROR,
                    "files_handler_document_processing_error",
                    peer_id=message.peer_id,
                    vk_user_id=get_vk_user_id(message),
                    error=str(e),
                )

    if new_attachments:
        attachments.extend(new_attachments)
        payload["attachments"] = attachments

        await set_state(
            message,
            AppealState.WAITING_FOR_FILES,
            reason="files_added_more_allowed",
            **payload,
        )

        await send_answer(
            message,
            f"✅ Файл{'ы' if len(new_attachments) > 1 else ''} добавлен{'ы' if len(new_attachments) > 1 else ''}! Всего файлов: {len(attachments)}\n\nМожете отправить еще файлы или нажать 'Пропустить' для завершения:",
            keyboard=get_files_kb(),
            event="files_added",
        )
    else:
        await send_answer(
            message,
            "Не удалось обработать файлы. Попробуйте отправить файлы заново или нажмите 'Пропустить':",
            keyboard=get_files_kb(),
            event="files_processing_failed",
        )

# функция для финализации обращения 
async def finalize_appeal(message: Message, payload: Dict[str, Any]):
    vk_user_id = get_vk_user_id(message)

    if "attachments" not in payload:
        payload["attachments"] = []

    appeal, registration = await build_appeal_from_payload(payload, vk_user_id)

    if not registration.request_ok:
        log_event(
            logging.ERROR,
            "finalize_appeal_registration_check_error",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
        )

        await send_answer(
            message,
            "Возникла ошибка при проверке регистрации. Попробуйте позже.",
            keyboard=get_navigation_kb(),
            event="final_registration_check_error",
        )
        return

    if not registration.registered:
        verified_users.discard(vk_user_id)

        log_event(
            logging.INFO,
            "finalize_appeal_user_not_registered_on_final_check",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            verified_users_count=len(verified_users),
        )

        await delete_state(message, reason="final_registration_check_not_registered")
        await send_registration_required(message)
        return

    if appeal is None:
        log_event(
            logging.ERROR,
            "finalize_appeal_appeal_none_after_build",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            payload=safe_payload(payload),
        )

        await delete_state(message, reason="appeal_build_failed")
        await send_answer(
            message,
            "Возникла ошибка при формировании обращения. Попробуйте позже.",
            keyboard=get_start_kb(),
            event="appeal_build_error",
        )
        return

    saved, appeal_number = await save_appeal_to_db(appeal)
    appeal_number_text = f"\nНомер заявки: №{appeal_number}" if appeal_number is not None else ""

    if not saved:
        log_event(
            logging.ERROR,
            "finalize_appeal_appeal_save_failed",
            peer_id=message.peer_id,
            vk_user_id=vk_user_id,
            payload=safe_payload(payload),
        )

        await set_state(
            message,
            AppealState.WAITING_FOR_FILES,
            reason="appeal_save_failed_retry_files",
            **payload,
        )
        await send_answer(
            message,
            "Возникла ошибка при отправке обращения. Попробуйте позже.",
            keyboard=get_files_kb(),
            event="appeal_send_error",
        )
        return

    await delete_state(message, reason="appeal_saved_successfully")

    log_event(
        logging.INFO,
        "finalize_appeal_appeal_flow_finished",
        peer_id=message.peer_id,
        vk_user_id=vk_user_id,
        appeal_type=appeal.type,
        attachments_count=len(appeal.attachments or []),
        appeal_number=appeal_number,
    )

    if appeal.type == AppealType.COMPLAINT:
        await send_answer(
            message,
            f"✅ Ваша жалоба успешно зарегистрирована!{appeal_number_text}",
            keyboard=get_start_kb(),
            event="complaint_saved_success",
        )
    elif appeal.type == AppealType.SUGGESTION:
        await send_answer(
            message,
            f"✅ Ваше предложение успешно зарегистрировано!{appeal_number_text}",
            keyboard=get_start_kb(),
            event="suggestion_saved_success",
        )
    elif appeal.type == AppealType.QUESTION:
        await send_answer(
            message,
            f"✅ Ваш вопрос успешно зарегистрирован!{appeal_number_text}",
            keyboard=get_start_kb(),
            event="question_saved_success",
        )
    elif appeal.type == AppealType.REQUEST:
        await send_answer(
            message,
            f"✅ Ваш запрос успешно зарегистрирован!{appeal_number_text}",
            keyboard=get_start_kb(),
            event="request_saved_success",
        )

# ----------------------------
# --- резервный обработчик ---
# ----------------------------
@bot.on.message()
async def fallback_handler(message: Message):
    log_handler_entry("fallback_handler", message)

    text = (message.text or "").strip()

    if text == CHECK_REGISTRATION_BUTTON:
        log_event(
            logging.WARNING,
            "fallback_received_registration_check_button",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            state=get_current_state_name(message),
        )

        await process_registration_check(message)
        return

    if text == START_BUTTON:
        log_event(
            logging.WARNING,
            "fallback_received_start_button",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            state=get_current_state_name(message),
        )

        await start_handler(message)
        return

    if message.state_peer:
        log_event(
            logging.INFO,
            "fallback_active_state",
            peer_id=message.peer_id,
            vk_user_id=get_vk_user_id(message),
            state=get_current_state_name(message),
        )

        await send_answer(
            message,
            "Пожалуйста, следуйте инструкциям или используйте кнопки «Назад» / «Отмена».",
            keyboard=get_navigation_kb(),
            event="fallback_active_state",
        )
        return

    log_event(
        logging.INFO,
        "fallback_no_state_registration_intro",
        peer_id=message.peer_id,
        vk_user_id=get_vk_user_id(message),
    )

    await send_registration_intro(message)


if __name__ == "__main__":
    log_event(
        logging.INFO,
        "bot_starting",
        api_base_url=API_BASE_URL,
        site_base_url=SITE_BASE_URL,
        registration_path=REGISTRATION_PATH,
        appeal_enum_format=APPEAL_ENUM_FORMAT,
    )

    bot.loop_wrapper.add_task(kafka_listener_task())
    print("бот «предложалоба» запущен")
    bot.run_forever()