import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from functools import wraps
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import aiohttp
from dotenv import load_dotenv
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, BaseStateGroup


# --- модели данных ---

class AppealType(str, Enum):
    COMPLAINT = "Жалоба"
    SUGGESTION = "Предложение"


class LocationType(str, Enum):
    CAMPUS = "Студгородок"
    DORMITORY = "Общежитие"
    EDUCATIONAL_CORPUS = "Учебный корпус"
    NOT_APPLICABLE = "Не применимо"


class ProblemCategory(str, Enum):
    RESETTLEMENT = "Расселение"
    BATHROOM = "Санузел"
    ELECTRICITY = "Электрика"
    PLUMBING = "Сантехника"
    OTHER = "Другое"
    NOT_APPLICABLE = "Не применимо"


class AppealStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


@dataclass
class Appeal:
    type: AppealType
    description: str
    personal_data_consent: bool
    vk_user_id: int

    campus_location: LocationType = LocationType.NOT_APPLICABLE
    problem_category: ProblemCategory = ProblemCategory.NOT_APPLICABLE
    timeframe: Optional[str] = None

    id: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: AppealStatus = AppealStatus.NEW

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)

        if data.get("id") is None:
            data.pop("id", None)

        for key, value in list(data.items()):
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()

        return data


@dataclass
class RegistrationResult:
    request_ok: bool
    registered: bool
    data: Dict[str, Any] = field(default_factory=dict)


# --- настройки ---

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")


def build_api_base_url() -> str:
    base_url = os.getenv("BACKEND_BASE_URL", "http://app:8080").rstrip("/")
    api_prefix = os.getenv("BACKEND_API_PREFIX", "/api").strip("/")

    if api_prefix:
        return f"{base_url}/{api_prefix}"

    return base_url


API_BASE_URL = build_api_base_url()

SITE_BASE_URL = os.getenv(
    "SITE_BASE_URL",
    os.getenv("BACKEND_BASE_URL", "http://app:8080"),
).rstrip("/")

REGISTRATION_PATH = os.getenv("REGISTRATION_PATH", "/register")
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=float(os.getenv("HTTP_TIMEOUT_SECONDS", "10")))

START_BUTTON = "Начать"
CHECK_REGISTRATION_BUTTON = "Проверить регистрацию"
BACK_BUTTON = "Назад"
CANCEL_BUTTON = "Отмена"

if not TOKEN:
    raise ValueError("токен не найден. создайте файл .env и добавьте VK_TOKEN=ваш_токен")

bot = Bot(token=TOKEN)


def api_url(path: str) -> str:
    return f"{API_BASE_URL}/{path.lstrip('/')}"


def site_url(path: str) -> str:
    return f"{SITE_BASE_URL}/{path.lstrip('/')}"


# --- состояния ---

class AppealState(BaseStateGroup):
    WAITING_FOR_TYPE = 0
    WAITING_FOR_LOCATION = 1
    WAITING_FOR_CATEGORY = 2
    WAITING_FOR_TIMEFRAME = 3
    WAITING_FOR_DESCRIPTION = 4


# --- справочники ---

LOCATION_CATEGORIES: Dict[LocationType, List[ProblemCategory]] = {
    LocationType.DORMITORY: [
        ProblemCategory.RESETTLEMENT,
        ProblemCategory.BATHROOM,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.OTHER,
    ],
    LocationType.EDUCATIONAL_CORPUS: [
        ProblemCategory.BATHROOM,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.OTHER,
    ],
    LocationType.CAMPUS: [
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.OTHER,
    ],
}

VALID_TIMEFRAMES = [
    "В течение дня",
    "До 3 дней",
    "В течение недели",
    "Не срочно",
]


# --- утилиты ---

def get_vk_user_id(message: Message) -> int:
    return int(message.from_id or message.peer_id)


def add_query_params(url: str, params: Dict[str, Any]) -> str:
    parsed = urlparse(url)
    current_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    current_params.update({key: str(value) for key, value in params.items()})

    return urlunparse(parsed._replace(query=urlencode(current_params)))


def get_registration_url(vk_user_id: int) -> str:
    return add_query_params(
        site_url(REGISTRATION_PATH),
        {"vkUserId": vk_user_id},
    )


def enum_from_payload(enum_cls, value, default):
    if isinstance(value, enum_cls):
        return value

    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return default


def get_categories_for_location(location: LocationType) -> List[ProblemCategory]:
    return LOCATION_CATEGORIES.get(location, [ProblemCategory.OTHER])


def is_valid_description(text: Optional[str]) -> bool:
    return bool(text and len(text.strip()) >= 5)


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


def get_first_present(data: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = data.get(key)

        if value not in (None, ""):
            return str(value).strip()

    return None


def unwrap_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    for key in ("user", "data", "profile"):
        value = data.get(key)

        if isinstance(value, dict):
            return value

    return data


def get_registration_flag_from_dict(data: Dict[str, Any]) -> Optional[bool]:
    for key in ("registered", "isRegistered", "exists", "success"):
        if key in data:
            parsed = normalize_bool(data.get(key))

            if parsed is not None:
                return parsed

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
        user_data.get("last_name") or user_data.get("lastName"),
        user_data.get("first_name") or user_data.get("firstName"),
        user_data.get("middle_name") or user_data.get("middleName"),
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

    return {
        "contact_name": build_full_name(user_data),
        "contact_phone": get_first_present(
            user_data,
            "contact_phone",
            "contactPhone",
            "phone",
            "phoneNumber",
            "phone_number",
        ),
        "contact_email": contact_email,
        "personal_data_consent": consent,
    }


# --- api ---

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


def parse_registration_payload(payload: Any) -> RegistrationResult:
    if isinstance(payload, bool):
        return RegistrationResult(
            request_ok=True,
            registered=payload,
            data={},
        )

    if isinstance(payload, str):
        parsed = normalize_bool(payload)

        return RegistrationResult(
            request_ok=True,
            registered=bool(parsed),
            data={},
        )

    if isinstance(payload, dict):
        registered = get_registration_flag_from_dict(payload)
        user_data = unwrap_user_data(payload)

        if registered is None:
            registered = bool(user_data)

        return RegistrationResult(
            request_ok=True,
            registered=registered,
            data=user_data if registered else {},
        )

    return RegistrationResult(
        request_ok=True,
        registered=False,
        data={},
    )


async def check_user_registration(vk_user_id: int) -> RegistrationResult:
    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.get(
                api_url("/user/check"),
                params={"vkUserId": vk_user_id},
            ) as response:
                if response.status != 200:
                    print(f"ошибка проверки регистрации: статус {response.status}")
                    return RegistrationResult(
                        request_ok=False,
                        registered=False,
                        data={},
                    )

                payload = await read_response_payload(response)
                return parse_registration_payload(payload)

    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        print(f"ошибка проверки регистрации: {error}")

        return RegistrationResult(
            request_ok=False,
            registered=False,
            data={},
        )


async def send_to_backend(appeal: Appeal) -> bool:
    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.post(
                api_url("/appeals"),
                json=appeal.to_dict(),
            ) as response:
                if response.status in (200, 201):
                    print(f"успешно отправлено: статус {response.status}")
                    return True

                error_text = await response.text()
                print(f"ошибка отправки: статус {response.status}, ответ: {error_text}")
                return False

    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        print(f"ошибка отправки обращения: {error}")
        return False


async def save_appeal_to_db(appeal: Appeal) -> bool:
    return await send_to_backend(appeal)


async def build_appeal_from_payload(
    payload: Dict[str, Any],
    vk_user_id: int,
) -> Tuple[Optional[Appeal], RegistrationResult]:
    registration = await check_user_registration(vk_user_id)

    if not registration.request_ok or not registration.registered:
        return None, registration

    appeal_type = enum_from_payload(
        AppealType,
        payload.get("type"),
        AppealType.SUGGESTION,
    )

    campus_location = enum_from_payload(
        LocationType,
        payload.get("campus_location"),
        LocationType.NOT_APPLICABLE,
    )

    problem_category = enum_from_payload(
        ProblemCategory,
        payload.get("problem_category"),
        ProblemCategory.NOT_APPLICABLE,
    )

    if appeal_type == AppealType.SUGGESTION:
        campus_location = LocationType.NOT_APPLICABLE
        problem_category = ProblemCategory.NOT_APPLICABLE

    user_fields = get_user_contact_fields(registration.data)

    appeal = Appeal(
        type=appeal_type,
        description=str(payload.get("description", "")).strip(),
        personal_data_consent=user_fields["personal_data_consent"],
        vk_user_id=vk_user_id,
        campus_location=campus_location,
        problem_category=problem_category,
        timeframe=payload.get("timeframe"),
        contact_name=user_fields["contact_name"],
        contact_phone=user_fields["contact_phone"],
        contact_email=user_fields["contact_email"],
    )

    return appeal, registration


# --- клавиатуры ---

def get_registration_kb():
    return (
        Keyboard(one_time=False)
        .add(Text(CHECK_REGISTRATION_BUTTON), color=KeyboardButtonColor.POSITIVE)
        .get_json()
    )


def get_start_kb():
    return (
        Keyboard(one_time=False)
        .add(Text(START_BUTTON), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text(CHECK_REGISTRATION_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )


def get_type_kb():
    return (
        Keyboard(one_time=True)
        .add(Text(AppealType.COMPLAINT.value), color=KeyboardButtonColor.NEGATIVE)
        .add(Text(AppealType.SUGGESTION.value), color=KeyboardButtonColor.POSITIVE)
        .row()
        .add(Text(CANCEL_BUTTON), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )


def get_navigation_kb():
    return (
        Keyboard(one_time=True)
        .add(Text(BACK_BUTTON), color=KeyboardButtonColor.SECONDARY)
        .add(Text(CANCEL_BUTTON), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )


def add_navigation(kb: Keyboard) -> Keyboard:
    kb.row()
    kb.add(Text(BACK_BUTTON), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text(CANCEL_BUTTON), color=KeyboardButtonColor.NEGATIVE)

    return kb


def get_location_kb():
    kb = Keyboard(one_time=True)

    locations = [
        LocationType.CAMPUS,
        LocationType.DORMITORY,
        LocationType.EDUCATIONAL_CORPUS,
    ]

    for index, location in enumerate(locations):
        if index > 0:
            kb.row()

        kb.add(Text(location.value), color=KeyboardButtonColor.PRIMARY)

    return add_navigation(kb).get_json()


def get_category_kb(location: LocationType):
    kb = Keyboard(one_time=True)
    categories = get_categories_for_location(location)

    for index, category in enumerate(categories):
        if index > 0 and index % 2 == 0:
            kb.row()

        kb.add(Text(category.value), color=KeyboardButtonColor.SECONDARY)

    return add_navigation(kb).get_json()


def get_timeframe_kb():
    kb = (
        Keyboard(one_time=True)
        .add(Text("В течение дня"), color=KeyboardButtonColor.PRIMARY)
        .add(Text("До 3 дней"), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("В течение недели"), color=KeyboardButtonColor.SECONDARY)
        .add(Text("Не срочно"), color=KeyboardButtonColor.SECONDARY)
    )

    return add_navigation(kb).get_json()


# --- регистрация ---
verified_users: set[int] = set()
registration_intro_sent_users: set[int] = set()


async def send_registration_intro(message: Message):
    vk_user_id = get_vk_user_id(message)
    registration_intro_sent_users.add(vk_user_id)

    registration_url = get_registration_url(vk_user_id)

    text = (
        "Добро пожаловать в модуль «Предложалоба».\n\n"
        "Перед отправкой обращения нужно зарегистрироваться на сайте.\n\n"
        f"Ссылка на регистрацию:\n{registration_url}\n\n"
        "После регистрации нажмите «Проверить регистрацию»."
    )

    await message.answer(text, keyboard=get_registration_kb())


async def send_registration_required(message: Message):
    vk_user_id = get_vk_user_id(message)
    registration_url = get_registration_url(vk_user_id)

    text = (
        "Регистрация не найдена.\n\n"
        "Перед отправкой обращения нужно зарегистрироваться на сайте.\n\n"
        f"Ссылка на регистрацию:\n{registration_url}\n\n"
        "После регистрации нажмите «Проверить регистрацию»."
    )

    await message.answer(text, keyboard=get_registration_kb())


async def send_registration_error(message: Message):
    await message.answer(
        "Возникла ошибка при проверке регистрации. Попробуйте позже.",
        keyboard=get_registration_kb(),
    )


async def require_registered(message: Message) -> Optional[RegistrationResult]:
    vk_user_id = get_vk_user_id(message)
    result = await check_user_registration(vk_user_id)

    if not result.request_ok:
        await send_registration_error(message)
        return None

    if not result.registered:
        verified_users.discard(vk_user_id)
        await send_registration_required(message)
        return None

    verified_users.add(vk_user_id)
    return result


async def start_appeal_flow(message: Message):
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)

    await message.answer(
        "Регистрация подтверждена.\nВыберите тип обращения:",
        keyboard=get_type_kb(),
    )


async def process_registration_check(message: Message) -> bool:
    vk_user_id = get_vk_user_id(message)
    result = await check_user_registration(vk_user_id)

    if not result.request_ok:
        await send_registration_error(message)
        return False

    if not result.registered:
        verified_users.discard(vk_user_id)
        await send_registration_required(message)
        return False

    verified_users.add(vk_user_id)

    if message.state_peer:
        await message.answer(
            "Регистрация подтверждена. Продолжайте текущий шаг или нажмите «Отмена».",
            keyboard=get_navigation_kb(),
        )
        return True

    await start_appeal_flow(message)
    return True


# --- навигация ---

def handle_navigation(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        text = (message.text or "").strip()

        if text == CANCEL_BUTTON:
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer(
                "Действие отменено. Нажмите «Начать», чтобы начать заново.",
                keyboard=get_start_kb(),
            )
            return

        if text == BACK_BUTTON:
            await back_action(message)
            return

        if text == CHECK_REGISTRATION_BUTTON:
            await process_registration_check(message)
            return

        await func(message, *args, **kwargs)

    return wrapper


async def back_action(message: Message):
    if not message.state_peer:
        return

    current_state = message.state_peer.state
    payload = message.state_peer.payload or {}
    appeal_type = enum_from_payload(AppealType, payload.get("type"), None)

    if current_state == AppealState.WAITING_FOR_LOCATION:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
        await message.answer("Выберите тип обращения:", keyboard=get_type_kb())
        return

    if current_state == AppealState.WAITING_FOR_CATEGORY:
        await bot.state_dispenser.set(
            message.peer_id,
            AppealState.WAITING_FOR_LOCATION,
            **payload,
        )
        await message.answer("Выберите локацию проблемы:", keyboard=get_location_kb())
        return

    if current_state == AppealState.WAITING_FOR_TIMEFRAME:
        location = enum_from_payload(
            LocationType,
            payload.get("campus_location"),
            LocationType.NOT_APPLICABLE,
        )

        await bot.state_dispenser.set(
            message.peer_id,
            AppealState.WAITING_FOR_CATEGORY,
            **payload,
        )
        await message.answer(
            "Выберите категорию проблемы:",
            keyboard=get_category_kb(location),
        )
        return

    if current_state == AppealState.WAITING_FOR_DESCRIPTION:
        if appeal_type == AppealType.COMPLAINT:
            await bot.state_dispenser.set(
                message.peer_id,
                AppealState.WAITING_FOR_TIMEFRAME,
                **payload,
            )
            await message.answer("Укажите ориентировочные сроки:", keyboard=get_timeframe_kb())
        else:
            await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
            await message.answer("Выберите тип обращения:", keyboard=get_type_kb())

        return

    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
    await message.answer("Выберите тип обращения:", keyboard=get_type_kb())


# --- обработчики ---

@bot.on.message(text=[CHECK_REGISTRATION_BUTTON])
async def check_registration_handler(message: Message):
    await process_registration_check(message)


@bot.on.message(text=[START_BUTTON, "Привет", "предложалоба", "Предложалоба"])
async def start_handler(message: Message):
    if message.state_peer:
        await message.answer(
            "Сначала завершите текущее обращение или нажмите «Отмена».",
            keyboard=get_navigation_kb(),
        )
        return

    vk_user_id = get_vk_user_id(message)

    # первое сообщение не проверяет регистрацию через бэк
    if vk_user_id not in registration_intro_sent_users and vk_user_id not in verified_users:
        await send_registration_intro(message)
        return

    # после подтвержденной регистрации можно сразу начинать
    if vk_user_id in verified_users:
        await start_appeal_flow(message)
        return

    # если приветствие уже показывали, но регистрацию еще не подтвердили
    await send_registration_intro(message)


@bot.on.message(state=AppealState.WAITING_FOR_TYPE)
async def type_handler(message: Message):
    text = (message.text or "").strip()

    if text == CANCEL_BUTTON:
        await bot.state_dispenser.delete(message.peer_id)
        await message.answer(
            "Действие отменено. Нажмите «Начать», чтобы начать заново.",
            keyboard=get_start_kb(),
        )
        return

    if text == BACK_BUTTON:
        await message.answer("Вы уже на первом шаге.", keyboard=get_type_kb())
        return

    if text == CHECK_REGISTRATION_BUTTON:
        await process_registration_check(message)
        return

    # на этом шаге не дергаем бэк, потому что проверка уже была
    if get_vk_user_id(message) not in verified_users:
        await send_registration_intro(message)
        return

    if text == AppealType.COMPLAINT.value:
        await bot.state_dispenser.set(
            message.peer_id,
            AppealState.WAITING_FOR_LOCATION,
            type=AppealType.COMPLAINT.value,
        )
        await message.answer("Выберите локацию проблемы:", keyboard=get_location_kb())
        return

    if text == AppealType.SUGGESTION.value:
        await bot.state_dispenser.set(
            message.peer_id,
            AppealState.WAITING_FOR_DESCRIPTION,
            type=AppealType.SUGGESTION.value,
        )
        await message.answer("Опишите ваше предложение:", keyboard=get_navigation_kb())
        return

    await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_type_kb())


@bot.on.message(state=AppealState.WAITING_FOR_LOCATION)
@handle_navigation
async def location_handler(message: Message):
    text = (message.text or "").strip()

    try:
        location = LocationType(text)
    except ValueError:
        await message.answer("Выберите локацию из списка.", keyboard=get_location_kb())
        return

    payload = (message.state_peer.payload or {}).copy()
    payload["campus_location"] = location.value

    await bot.state_dispenser.set(
        message.peer_id,
        AppealState.WAITING_FOR_CATEGORY,
        **payload,
    )

    await message.answer(
        "Выберите категорию проблемы:",
        keyboard=get_category_kb(location),
    )


@bot.on.message(state=AppealState.WAITING_FOR_CATEGORY)
@handle_navigation
async def category_handler(message: Message):
    text = (message.text or "").strip()
    payload = (message.state_peer.payload or {}).copy()

    location = enum_from_payload(
        LocationType,
        payload.get("campus_location"),
        LocationType.NOT_APPLICABLE,
    )

    allowed_categories = get_categories_for_location(location)

    try:
        category = ProblemCategory(text)
    except ValueError:
        await message.answer(
            "Выберите категорию из списка.",
            keyboard=get_category_kb(location),
        )
        return

    if category not in allowed_categories:
        await message.answer(
            "Эта категория недоступна для выбранной локации.",
            keyboard=get_category_kb(location),
        )
        return

    payload["problem_category"] = category.value

    await bot.state_dispenser.set(
        message.peer_id,
        AppealState.WAITING_FOR_TIMEFRAME,
        **payload,
    )

    await message.answer("Укажите ориентировочные сроки:", keyboard=get_timeframe_kb())


@bot.on.message(state=AppealState.WAITING_FOR_TIMEFRAME)
@handle_navigation
async def timeframe_handler(message: Message):
    text = (message.text or "").strip()

    if text not in VALID_TIMEFRAMES:
        await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_timeframe_kb())
        return

    payload = (message.state_peer.payload or {}).copy()
    payload["timeframe"] = text

    await bot.state_dispenser.set(
        message.peer_id,
        AppealState.WAITING_FOR_DESCRIPTION,
        **payload,
    )

    await message.answer("Опишите суть вашей проблемы подробно:", keyboard=get_navigation_kb())


@bot.on.message(state=AppealState.WAITING_FOR_DESCRIPTION)
@handle_navigation
async def description_handler(message: Message):
    text = (message.text or "").strip()

    if not is_valid_description(text):
        await message.answer(
            "Описание слишком короткое. Опишите обращение подробнее:",
            keyboard=get_navigation_kb(),
        )
        return

    payload = (message.state_peer.payload or {}).copy()
    payload["description"] = text

    vk_user_id = get_vk_user_id(message)
    appeal, registration = await build_appeal_from_payload(payload, vk_user_id)

    if not registration.request_ok:
        await message.answer(
            "Возникла ошибка при проверке регистрации. Попробуйте позже.",
            keyboard=get_navigation_kb(),
        )
        return

    if not registration.registered:
        await bot.state_dispenser.delete(message.peer_id)
        await send_registration_required(message)
        return

    if appeal is None:
        await bot.state_dispenser.delete(message.peer_id)
        await message.answer(
            "Возникла ошибка при формировании обращения. Попробуйте позже.",
            keyboard=get_start_kb(),
        )
        return

    saved = await save_appeal_to_db(appeal)

    if not saved:
        await bot.state_dispenser.set(
            message.peer_id,
            AppealState.WAITING_FOR_DESCRIPTION,
            **payload,
        )
        await message.answer(
            "Возникла ошибка при отправке обращения. Попробуйте позже.",
            keyboard=get_navigation_kb(),
        )
        return

    await bot.state_dispenser.delete(message.peer_id)

    if appeal.type == AppealType.COMPLAINT:
        await message.answer(
            "✅ Ваша жалоба успешно зарегистрирована!",
            keyboard=get_start_kb(),
        )
    else:
        await message.answer(
            "✅ Ваше предложение успешно зарегистрировано!",
            keyboard=get_start_kb(),
        )


# --- резервный обработчик ---

@bot.on.message()
async def fallback_handler(message: Message):
    if message.state_peer:
        await message.answer(
            "Пожалуйста, следуйте инструкциям или используйте кнопки «Назад» / «Отмена».",
            keyboard=get_navigation_kb(),
        )
        return

    # первое произвольное сообщение не должно обращаться к бэку
    await send_registration_intro(message)


if __name__ == "__main__":
    print("бот «предложалоба» запущен")
    bot.run_forever()