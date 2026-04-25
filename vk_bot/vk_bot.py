import uuid
import json
import os
import re
import aiohttp
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from functools import wraps

from dotenv import load_dotenv
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, BaseStateGroup

# --- 1. ОПРЕДЕЛЕНИЕ ENUM И МОДЕЛЕЙ ДАННЫХ ---

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
        if data.get('id') is None: data.pop('id', None)
        for key, value in data.items():
            if isinstance(value, Enum): data[key] = value.value
            elif isinstance(value, datetime): data[key] = value.isoformat()
        return data

# --- 2. ВАЛИДАТОРЫ ---

def is_valid_name(name: str) -> bool:
    return bool(re.match(r"^[A-Za-zА-Яа-яЁё\s\-]{2,}$", name.strip()))

def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r"^(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$", phone.strip()))

def is_valid_contact_link(contact: str) -> bool:
    contact = contact.strip()
    if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact): return True
    if re.match(r"^(https?://)?(www\.)?vk\.com/.*$", contact): return True
    if re.match(r"^(https?://)?(www\.)?t\.me/.*$", contact): return True
    if contact.startswith("@") and len(contact) > 1: return True
    return False

# --- 3. НАСТРОЙКА БОТА И FSM ---

load_dotenv()
TOKEN = os.getenv("VK_TOKEN")

def build_api_base_url() -> str:
    base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8080").rstrip("/")
    api_prefix = os.getenv("BACKEND_API_PREFIX", "/api").strip("/")
    if api_prefix:
        return f"{base_url}/{api_prefix}"
    return base_url


API_BASE_URL = build_api_base_url()


def api_url(path: str) -> str:
    return f"{API_BASE_URL}/{path.lstrip('/')}"

if not TOKEN:
    raise ValueError("Токен не найден! Создайте файл .env и добавьте VK_TOKEN=ваш_токен")

bot = Bot(token=TOKEN)
print("VK_TOKEN =", TOKEN)

class AppealState(BaseStateGroup):
    WAITING_FOR_TYPE = 0
    WAITING_FOR_LOCATION = 1
    WAITING_FOR_CATEGORY = 2
    WAITING_FOR_TIMEFRAME = 3
    WAITING_FOR_DESCRIPTION = 4
    WAITING_FOR_CONSENT = 5
    WAITING_FOR_NAME = 6
    WAITING_FOR_PHONE = 7
    WAITING_FOR_CONTACT_LINK = 8

# --- 4. ФУНКЦИИ API ---

async def send_to_backend(appeal: Appeal):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url("/appeals"), json=appeal.to_dict()) as response:
                if response.status in [200, 201]: print(f"✅ Успешно отправлено (Статус {response.status})")
                else: print(f"❌ Ошибка отправки (Статус {response.status}): {await response.text()}")
    except Exception as e:
        print(f"⚠️ Ошибка соединения с бэкендом: {e}")

async def save_appeal_to_db(appeal: Appeal):
    await send_to_backend(appeal)

# --- 5. КЛАВИАТУРЫ ---

def get_start_kb():
    return Keyboard(one_time=False).add(Text("Начать"), color=KeyboardButtonColor.PRIMARY).get_json()

def get_type_kb():
    return (Keyboard(one_time=True)
            .add(Text(AppealType.COMPLAINT.value), color=KeyboardButtonColor.NEGATIVE)
            .add(Text(AppealType.SUGGESTION.value), color=KeyboardButtonColor.POSITIVE)
            .get_json())

def get_navigation_kb():
    return (Keyboard(one_time=True)
            .add(Text("Назад"), color=KeyboardButtonColor.SECONDARY)
            .add(Text("Отмена"), color=KeyboardButtonColor.NEGATIVE)
            .get_json())

def add_navigation(kb: Keyboard) -> Keyboard:
    kb.row()
    kb.add(Text("Назад"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return kb

def get_location_kb():
    kb = Keyboard(one_time=True)
    for loc in [LocationType.CAMPUS, LocationType.DORMITORY, LocationType.EDUCATIONAL_CORPUS]:
        kb.add(Text(loc.value), color=KeyboardButtonColor.PRIMARY).row()
    return add_navigation(kb).get_json()

def get_category_kb():
    kb = Keyboard(one_time=True)
    categories = [ProblemCategory.RESETTLEMENT, ProblemCategory.BATHROOM,
                  ProblemCategory.ELECTRICITY, ProblemCategory.PLUMBING, ProblemCategory.OTHER]
    for i, cat in enumerate(categories):
        kb.add(Text(cat.value), color=KeyboardButtonColor.SECONDARY)
        if i % 2 != 0: kb.row()
    return add_navigation(kb).get_json()

def get_timeframe_kb():
    kb = (Keyboard(one_time=True)
            .add(Text("В течение дня"), color=KeyboardButtonColor.PRIMARY)
            .add(Text("До 3 дней"), color=KeyboardButtonColor.PRIMARY).row()
            .add(Text("В течение недели"), color=KeyboardButtonColor.SECONDARY)
            .add(Text("Не срочно"), color=KeyboardButtonColor.SECONDARY))
    return add_navigation(kb).get_json()

def get_consent_kb():
    kb = Keyboard(one_time=True).add(Text("Согласен"), color=KeyboardButtonColor.POSITIVE).add(Text("Не согласен"), color=KeyboardButtonColor.NEGATIVE)
    return add_navigation(kb).get_json()

# --- 6. ОБРАБОТЧИК НАВИГАЦИИ (ДЕКОРАТОР) ---

def handle_navigation(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if message.text == "Отмена":
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer("Действие отменено. Нажмите «Начать», чтобы начать заново.", keyboard=get_start_kb())
            return
        if message.text == "Назад":
            await back_action(message)
            return
        await func(message, *args, **kwargs)
    return wrapper

async def back_action(message: Message):
    if not message.state_peer: return

    current_state = message.state_peer.state
    payload = message.state_peer.payload
    appeal_type = payload.get("type")

    if current_state == AppealState.WAITING_FOR_LOCATION:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
        await message.answer("Выберите тип обращения:", keyboard=get_type_kb())

    elif current_state == AppealState.WAITING_FOR_CATEGORY:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_LOCATION, **payload)
        await message.answer("Выберите локацию проблемы:", keyboard=get_location_kb())

    elif current_state == AppealState.WAITING_FOR_TIMEFRAME:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CATEGORY, **payload)
        await message.answer("Выберите категорию проблемы:", keyboard=get_category_kb())

    elif current_state == AppealState.WAITING_FOR_DESCRIPTION:
        if appeal_type == AppealType.COMPLAINT:
            await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TIMEFRAME, **payload)
            await message.answer("Укажите ориентировочные сроки:", keyboard=get_timeframe_kb())
        else:
            await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
            await message.answer("Выберите тип обращения:", keyboard=get_type_kb())

    elif current_state == AppealState.WAITING_FOR_CONSENT:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_DESCRIPTION, **payload)
        await message.answer("Опишите суть обращения подробно:", keyboard=get_navigation_kb())

    elif current_state == AppealState.WAITING_FOR_NAME:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CONSENT, **payload)
        consent_text = ("Даете ли вы согласие на обработку персональных данных?\n\n"
                        "Ссылка на политику: https://example.com/privacy-policy")
        await message.answer(consent_text, keyboard=get_consent_kb())

    elif current_state == AppealState.WAITING_FOR_PHONE:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_NAME, **payload)
        await message.answer("Укажите ваши ФИО:", keyboard=get_navigation_kb())

    elif current_state == AppealState.WAITING_FOR_CONTACT_LINK:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_PHONE, **payload)
        await message.answer("Укажите ваш номер телефона:", keyboard=get_navigation_kb())

# --- 7. ХЭНДЛЕРЫ ШАГОВ ---

@bot.on.message(text=["Начать", "Привет", "Предложалоба"])
async def start_handler(message: Message):
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
    await message.answer("Добро пожаловать в модуль 'Предложалоба'.\nВыберите тип обращения:", keyboard=get_type_kb())

@bot.on.message(state=AppealState.WAITING_FOR_TYPE)
async def type_handler(message: Message):
    if message.text == "Назад" or message.text == "Отмена": return
    if message.text == AppealType.COMPLAINT.value:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_LOCATION, type=AppealType.COMPLAINT)
        await message.answer("Выберите локацию проблемы:", keyboard=get_location_kb())
    elif message.text == AppealType.SUGGESTION.value:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_DESCRIPTION, type=AppealType.SUGGESTION)
        await message.answer("Опишите ваше предложение:", keyboard=get_navigation_kb())
    else:
        await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_type_kb())

@bot.on.message(state=AppealState.WAITING_FOR_LOCATION)
@handle_navigation
async def location_handler(message: Message):
    try:
        loc = LocationType(message.text)
        payload = message.state_peer.payload.copy()
        payload["campus_location"] = loc
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CATEGORY, **payload)
        await message.answer("Выберите категорию проблемы:", keyboard=get_category_kb())
    except ValueError:
        await message.answer("Выберите локацию из списка.", keyboard=get_location_kb())

@bot.on.message(state=AppealState.WAITING_FOR_CATEGORY)
@handle_navigation
async def category_handler(message: Message):
    try:
        cat = ProblemCategory(message.text)
        payload = message.state_peer.payload.copy()
        payload["problem_category"] = cat
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TIMEFRAME, **payload)
        await message.answer("Укажите ориентировочные сроки:", keyboard=get_timeframe_kb())
    except ValueError:
        await message.answer("Выберите категорию из списка.", keyboard=get_category_kb())

@bot.on.message(state=AppealState.WAITING_FOR_TIMEFRAME)
@handle_navigation
async def timeframe_handler(message: Message):
    valid_timeframes = ["В течение дня", "До 3 дней", "В течение недели", "Не срочно"]
    if message.text not in valid_timeframes:
        await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_timeframe_kb())
        return
    payload = message.state_peer.payload.copy()
    payload["timeframe"] = message.text
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_DESCRIPTION, **payload)
    await message.answer("Опишите суть вашей проблемы подробно:", keyboard=get_navigation_kb())

@bot.on.message(state=AppealState.WAITING_FOR_DESCRIPTION)
@handle_navigation
async def description_handler(message: Message):
    payload = message.state_peer.payload.copy()
    payload["description"] = message.text
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CONSENT, **payload)
    consent_text = ("Даете ли вы согласие на обработку персональных данных?\n\n"
                    "Ознакомиться с политикой можно по ссылке: https://example.com/privacy-policy")
    await message.answer(consent_text, keyboard=get_consent_kb())

@bot.on.message(state=AppealState.WAITING_FOR_CONSENT)
@handle_navigation
async def consent_handler(message: Message):
    payload = message.state_peer.payload
    if message.text.lower() == "согласен":
        new_payload = payload.copy()
        new_payload["personal_data_consent"] = True
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_NAME, **new_payload)
        await message.answer("Укажите ваши ФИО:", keyboard=get_navigation_kb())
    elif message.text.lower() == "не согласен":
        if payload.get("type") == AppealType.SUGGESTION:
            appeal = Appeal(
                type=payload.get("type"), description=payload.get("description"),
                personal_data_consent=False, timeframe=payload.get("timeframe"),
                vk_user_id=message.peer_id
            )
            await save_appeal_to_db(appeal)
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer("✅ Ваше предложение отправлено анонимно.", keyboard=get_start_kb())
        else:
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer("❌ Без согласия нельзя принять жалобу.", keyboard=get_start_kb())
    else:
        await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_consent_kb())

@bot.on.message(state=AppealState.WAITING_FOR_NAME)
@handle_navigation
async def name_handler(message: Message):
    if not is_valid_name(message.text):
        await message.answer("⚠️ Некорректные ФИО. Введите, пожалуйста, снова:")
        return
    payload = message.state_peer.payload.copy()
    payload["contact_name"] = message.text
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_PHONE, **payload)
    await message.answer("Укажите ваш номер телефона (Например: +79991234567):", keyboard=get_navigation_kb())

@bot.on.message(state=AppealState.WAITING_FOR_PHONE)
@handle_navigation
async def phone_handler(message: Message):
    if not is_valid_phone(message.text):
        await message.answer("⚠️ Неверный формат телефона. Введите, пожалуйста, снова:")
        return
    payload = message.state_peer.payload.copy()
    payload["contact_phone"] = message.text
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CONTACT_LINK, **payload)
    await message.answer("Укажите ваш E-mail, ссылку на страницу ВК или юзернейм Telegram:", keyboard=get_navigation_kb())

@bot.on.message(state=AppealState.WAITING_FOR_CONTACT_LINK)
@handle_navigation
async def contact_link_handler(message: Message):
    if not is_valid_contact_link(message.text):
        await message.answer("⚠️ Неверный формат. Укажите, пожалуйста, снова:")
        return
    payload = message.state_peer.payload
    appeal = Appeal(
        type=payload.get("type"),
        campus_location=payload.get("campus_location", LocationType.NOT_APPLICABLE),
        problem_category=payload.get("problem_category", ProblemCategory.NOT_APPLICABLE),
        timeframe=payload.get("timeframe"), description=payload.get("description"),
        contact_name=payload.get("contact_name"), contact_phone=payload.get("contact_phone"),
        contact_email=message.text, personal_data_consent=True, vk_user_id=message.peer_id
    )
    await save_appeal_to_db(appeal)
    await bot.state_dispenser.delete(message.peer_id)
    await message.answer("✅ Ваше обращение успешно зарегистрировано!", keyboard=get_start_kb())

# --- 8. РЕЗЕРВНЫЙ ХЭНДЛЕР ---

@bot.on.message()
async def fallback_handler(message: Message):
    if message.state_peer:
        await message.answer("Пожалуйста, следуйте инструкциям или используйте кнопки «Назад» / «Отмена».")
    else:
        await message.answer("Я бот приема обращений. Для создания нового обращения нажмите «Начать».", keyboard=get_start_kb())

if __name__ == "__main__":
    print("VK_TOKEN", TOKEN)
    print("Бот 'Предложалоба' запущен!")
    bot.run_forever()