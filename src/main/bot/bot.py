import uuid
import json
import os
import re
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict

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
        
        if data.get('id') is None:
            data.pop('id', None)
            
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
                
        return data

# --- 2. ВАЛИДАТОРЫ ---

def is_valid_phone(phone: str) -> bool:
    pattern = re.compile(r"^(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$")
    return bool(pattern.match(phone.strip()))

def is_valid_contact_link(contact: str) -> bool:
    contact = contact.strip()
    if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact): return True
    if re.match(r"^(https?://)?(www\.)?vk\.com/.*$", contact): return True
    if re.match(r"^(https?://)?(www\.)?t\.me/.*$", contact): return True
    if contact.startswith("@") and len(contact) > 1: return True
    return False

# --- 3. НАСТРОЙКА БОТА И FSM ---

# Ищем и загружаем .env файл (будет искать в текущей папке и выше по дереву)
load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
if not TOKEN:
    raise ValueError("Токен не найден! Пожалуйста, создайте файл .env и добавьте туда VK_TOKEN=ваш_токен")

bot = Bot(token=TOKEN)

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

# --- 4. ФУНКЦИЯ СОЗДАНИЯ DTO ---

DTO_FOLDER = "dtos"

def create_dto_file(appeal: Appeal):
    # Папка dtos будет создаваться автоматически, если вы её удалили
    os.makedirs(DTO_FOLDER, exist_ok=True)
    
    appeal_data = appeal.to_dict()
    if appeal.id:
        appeal_data["id"] = str(appeal.id)

    filename_id = appeal.id if appeal.id else str(uuid.uuid4())
    filename = os.path.join(DTO_FOLDER, f"appeal_{filename_id}.json")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(appeal_data, f, ensure_ascii=False, indent=4)
        print(f"DTO файл создан: {filename}")
    except Exception as e:
        print(f"Ошибка при создании DTO файла {filename}: {e}")

def save_appeal_to_db(appeal: Appeal):
    create_dto_file(appeal)

# --- 5. КЛАВИАТУРЫ ---

def get_start_kb():
    return (Keyboard(one_time=False)
            .add(Text("Начать"), color=KeyboardButtonColor.PRIMARY)
            .get_json())

def get_type_kb():
    return (Keyboard(one_time=True)
            .add(Text(AppealType.COMPLAINT.value), color=KeyboardButtonColor.NEGATIVE)
            .add(Text(AppealType.SUGGESTION.value), color=KeyboardButtonColor.POSITIVE)
            .get_json())

def get_location_kb():
    kb = Keyboard(one_time=True)
    for loc in[LocationType.CAMPUS, LocationType.DORMITORY, LocationType.EDUCATIONAL_CORPUS]:
        kb.add(Text(loc.value), color=KeyboardButtonColor.PRIMARY)
        kb.row()
    return kb.get_json()

def get_category_kb():
    kb = Keyboard(one_time=True)
    categories =[ProblemCategory.RESETTLEMENT, ProblemCategory.BATHROOM, 
                  ProblemCategory.ELECTRICITY, ProblemCategory.PLUMBING, ProblemCategory.OTHER]
    for i, cat in enumerate(categories):
        kb.add(Text(cat.value), color=KeyboardButtonColor.SECONDARY)
        if i % 2 != 0: kb.row()
    return kb.get_json()

def get_timeframe_kb():
    return (Keyboard(one_time=True)
            .add(Text("В течение дня"), color=KeyboardButtonColor.PRIMARY)
            .add(Text("До 3 дней"), color=KeyboardButtonColor.PRIMARY).row()
            .add(Text("В течение недели"), color=KeyboardButtonColor.SECONDARY)
            .add(Text("Не срочно"), color=KeyboardButtonColor.SECONDARY)
            .get_json())

def get_consent_kb():
    return (Keyboard(one_time=True)
            .add(Text("Согласен"), color=KeyboardButtonColor.POSITIVE)
            .add(Text("Не согласен"), color=KeyboardButtonColor.NEGATIVE)
            .get_json())

def get_empty_kb():
    return Keyboard().get_json()

# --- 6. ХЭНДЛЕРЫ ---

@bot.on.message(text=["Начать", "Привет", "Предложалоба"])
async def start_handler(message: Message):
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TYPE)
    await message.answer("Добро пожаловать в модуль 'Предложалоба'.\nВыберите тип обращения:", keyboard=get_type_kb())

@bot.on.message(state=AppealState.WAITING_FOR_TYPE)
async def type_handler(message: Message):
    if message.text == AppealType.COMPLAINT.value:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_LOCATION, type=AppealType.COMPLAINT)
        await message.answer("Выберите локацию проблемы:", keyboard=get_location_kb())
    elif message.text == AppealType.SUGGESTION.value:
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_DESCRIPTION, type=AppealType.SUGGESTION)
        await message.answer("Опишите ваше предложение в одном сообщении:", keyboard=get_empty_kb())
    else:
        await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_type_kb())

@bot.on.message(state=AppealState.WAITING_FOR_LOCATION)
async def location_handler(message: Message):
    try:
        loc = LocationType(message.text)
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CATEGORY, 
                                      **message.state_peer.payload, campus_location=loc)
        await message.answer("Выберите категорию проблемы:", keyboard=get_category_kb())
    except ValueError:
        await message.answer("Выберите локацию из списка ниже.", keyboard=get_location_kb())

@bot.on.message(state=AppealState.WAITING_FOR_CATEGORY)
async def category_handler(message: Message):
    try:
        cat = ProblemCategory(message.text)
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_TIMEFRAME, 
                                      **message.state_peer.payload, problem_category=cat)
        await message.answer("Укажите ориентировочные сроки (Выберите из кнопок):", keyboard=get_timeframe_kb())
    except ValueError:
        await message.answer("Выберите категорию из списка ниже.", keyboard=get_category_kb())

@bot.on.message(state=AppealState.WAITING_FOR_TIMEFRAME)
async def timeframe_handler(message: Message):
    valid_timeframes =["В течение дня", "До 3 дней", "В течение недели", "Не срочно"]
    if message.text not in valid_timeframes:
        await message.answer("Пожалуйста, воспользуйтесь кнопками для выбора сроков:", keyboard=get_timeframe_kb())
        return

    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_DESCRIPTION, 
                                  **message.state_peer.payload, timeframe=message.text)
    await message.answer("Опишите суть вашей проблемы подробно:", keyboard=get_empty_kb())

@bot.on.message(state=AppealState.WAITING_FOR_DESCRIPTION)
async def description_handler(message: Message):
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CONSENT, 
                                  **message.state_peer.payload, description=message.text)
    await message.answer("Даете ли вы согласие на обработку персональных данных?", keyboard=get_consent_kb())

@bot.on.message(state=AppealState.WAITING_FOR_CONSENT)
async def consent_handler(message: Message):
    payload = message.state_peer.payload
    appeal_type = payload.get("type")

    if message.text.lower() == "согласен":
        await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_NAME, **payload, personal_data_consent=True)
        await message.answer("Укажите ваши ФИО:", keyboard=get_empty_kb())
    elif message.text.lower() == "не согласен":
        if appeal_type == AppealType.SUGGESTION:
            appeal = Appeal(
                type=appeal_type,
                description=payload.get("description"),
                personal_data_consent=False,
                timeframe=payload.get("timeframe")
            )
            save_appeal_to_db(appeal)
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer("✅ Ваше предложение отправлено анонимно.", keyboard=get_start_kb())
        else:
            await bot.state_dispenser.delete(message.peer_id)
            await message.answer("❌ Без согласия на обработку персональных данных мы не можем принять жалобу. Процесс отменен.", keyboard=get_start_kb())
    else:
        await message.answer("Пожалуйста, воспользуйтесь кнопками.", keyboard=get_consent_kb())

@bot.on.message(state=AppealState.WAITING_FOR_NAME)
async def name_handler(message: Message):
    name = message.text
    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_PHONE, 
                                  **message.state_peer.payload, contact_name=name)
    await message.answer("Укажите ваш номер телефона (Например: +79991234567):", keyboard=get_empty_kb())

@bot.on.message(state=AppealState.WAITING_FOR_PHONE)
async def phone_handler(message: Message):
    phone = message.text
    
    if not is_valid_phone(phone):
        await message.answer("⚠️ Неверный формат телефона. Пожалуйста, введите корректный российский номер телефона:")
        return

    await bot.state_dispenser.set(message.peer_id, AppealState.WAITING_FOR_CONTACT_LINK, 
                                  **message.state_peer.payload, contact_phone=phone)
    await message.answer("Укажите ваш E-mail, ссылку на страницу ВК или юзернейм Telegram:", keyboard=get_empty_kb())

@bot.on.message(state=AppealState.WAITING_FOR_CONTACT_LINK)
async def contact_link_handler(message: Message):
    contact = message.text
    
    if not is_valid_contact_link(contact):
        await message.answer("⚠️ Неверный формат. Пожалуйста, укажите почту (email@mail.ru), ссылку ВК (vk.com/id) или юзернейм TG (@username):")
        return

    payload = message.state_peer.payload
    
    appeal = Appeal(
        type=payload.get("type"),
        campus_location=payload.get("campus_location", LocationType.NOT_APPLICABLE),
        problem_category=payload.get("problem_category", ProblemCategory.NOT_APPLICABLE),
        timeframe=payload.get("timeframe"),
        description=payload.get("description"),
        contact_name=payload.get("contact_name"),
        contact_phone=payload.get("contact_phone"),
        contact_email=contact,
        personal_data_consent=True
    )
    
    save_appeal_to_db(appeal)
    
    await bot.state_dispenser.delete(message.peer_id)
    await message.answer("✅ Ваше обращение успешно зарегистрировано! Вы можете отправить новое, нажав кнопку ниже.", keyboard=get_start_kb())

# --- 7. РЕЗЕРВНЫЙ ХЭНДЛЕР ---

@bot.on.message()
async def fallback_handler(message: Message):
    if message.state_peer is not None:
        await message.answer("Пожалуйста, ответьте на текущий вопрос, чтобы продолжить регистрацию обращения.")
    else:
        await message.answer("Я бот приема обращений. Для создания нового обращения нажмите кнопку «Начать».", keyboard=get_start_kb())

if __name__ == "__main__":
    print("Бот 'Предложалоба' запущен!")
    bot.run_forever()