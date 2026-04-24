import os
import re
import aiohttp
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Включаем логирование
logging.basicConfig(level=logging.INFO)

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
    tg_user_id: int  # Изменено с vk_user_id

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
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


# --- 2. ВАЛИДАТОРЫ ---


def is_valid_name(name: str) -> bool:
    return bool(re.match(r"^[A-Za-zА-Яа-яЁё\s\-]{2,}$", name.strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(
        re.match(
            r"^(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$",
            phone.strip(),
        )
    )


def is_valid_contact_link(contact: str) -> bool:
    contact = contact.strip()
    if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact):
        return True
    if re.match(r"^(https?://)?(www\.)?vk\.com/.*$", contact):
        return True
    if re.match(r"^(https?://)?(www\.)?t\.me/.*$", contact):
        return True
    if contact.startswith("@") and len(contact) > 1:
        return True
    return False


# --- 3. НАСТРОЙКА БОТА И FSM ---

load_dotenv()
TOKEN = os.getenv("TG_TOKEN")  # Изменено на TG_TOKEN
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9090/api/appeals")

if not TOKEN:
    raise ValueError(
        "Токен не найден! Создайте файл .env и добавьте TG_TOKEN=ваш_токен"
    )

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)


class AppealState(StatesGroup):
    waiting_for_type = State()
    waiting_for_location = State()
    waiting_for_category = State()
    waiting_for_timeframe = State()
    waiting_for_description = State()
    waiting_for_consent = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_contact_link = State()


# --- 4. ФУНКЦИИ API ---


async def send_to_backend(appeal: Appeal):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(BACKEND_URL, json=appeal.to_dict()) as response:
                if response.status in [200, 201]:
                    logging.info(f"✅ Успешно отправлено (Статус {response.status})")
                else:
                    logging.error(
                        f"❌ Ошибка отправки (Статус {response.status}): {await response.text()}"
                    )
    except Exception as e:
        logging.error(f"⚠️ Ошибка соединения с бэкендом: {e}")


async def save_appeal_to_db(appeal: Appeal):
    await send_to_backend(appeal)


# --- 5. КЛАВИАТУРЫ ---


def get_start_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Начать"))
    return builder.as_markup(resize_keyboard=True)


def get_type_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=AppealType.COMPLAINT.value))
    builder.add(KeyboardButton(text=AppealType.SUGGESTION.value))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def add_navigation(builder: ReplyKeyboardBuilder) -> ReplyKeyboardMarkup:
    builder.row(KeyboardButton(text="Назад"), KeyboardButton(text="Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_navigation_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    return add_navigation(builder)


def get_location_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for loc in [
        LocationType.CAMPUS,
        LocationType.DORMITORY,
        LocationType.EDUCATIONAL_CORPUS,
    ]:
        builder.add(KeyboardButton(text=loc.value))
    builder.adjust(1)
    return add_navigation(builder)


def get_category_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    categories = [
        ProblemCategory.RESETTLEMENT,
        ProblemCategory.BATHROOM,
        ProblemCategory.ELECTRICITY,
        ProblemCategory.PLUMBING,
        ProblemCategory.OTHER,
    ]
    for cat in categories:
        builder.add(KeyboardButton(text=cat.value))
    builder.adjust(2)
    return add_navigation(builder)


def get_timeframe_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="В течение дня"), KeyboardButton(text="До 3 дней"))
    builder.add(
        KeyboardButton(text="В течение недели"), KeyboardButton(text="Не срочно")
    )
    builder.adjust(2, 2)
    return add_navigation(builder)


def get_consent_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Согласен"), KeyboardButton(text="Не согласен"))
    builder.adjust(2)
    return add_navigation(builder)


# --- 6. ОБРАБОТЧИКИ НАВИГАЦИИ (ГЛОБАЛЬНЫЕ) ---


@router.message(F.text == "Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено. Нажмите «Начать», чтобы начать заново.",
        reply_markup=get_start_kb(),
    )


@router.message(F.text == "Назад")
async def back_action(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        return

    data = await state.get_data()
    appeal_type = data.get("type")

    if current_state == AppealState.waiting_for_location.state:
        await state.set_state(AppealState.waiting_for_type)
        await message.answer("Выберите тип обращения:", reply_markup=get_type_kb())

    elif current_state == AppealState.waiting_for_category.state:
        await state.set_state(AppealState.waiting_for_location)
        await message.answer(
            "Выберите локацию проблемы:", reply_markup=get_location_kb()
        )

    elif current_state == AppealState.waiting_for_timeframe.state:
        await state.set_state(AppealState.waiting_for_category)
        await message.answer(
            "Выберите категорию проблемы:", reply_markup=get_category_kb()
        )

    elif current_state == AppealState.waiting_for_description.state:
        if appeal_type == AppealType.COMPLAINT.value:
            await state.set_state(AppealState.waiting_for_timeframe)
            await message.answer(
                "Укажите ориентировочные сроки:", reply_markup=get_timeframe_kb()
            )
        else:
            await state.set_state(AppealState.waiting_for_type)
            await message.answer("Выберите тип обращения:", reply_markup=get_type_kb())

    elif current_state == AppealState.waiting_for_consent.state:
        await state.set_state(AppealState.waiting_for_description)
        await message.answer(
            "Опишите суть обращения подробно:", reply_markup=get_navigation_kb()
        )

    elif current_state == AppealState.waiting_for_name.state:
        await state.set_state(AppealState.waiting_for_consent)
        consent_text = (
            "Даете ли вы согласие на обработку персональных данных?\n\n"
            "Ссылка на политику: https://example.com/privacy-policy"
        )
        await message.answer(consent_text, reply_markup=get_consent_kb())

    elif current_state == AppealState.waiting_for_phone.state:
        await state.set_state(AppealState.waiting_for_name)
        await message.answer("Укажите ваши ФИО:", reply_markup=get_navigation_kb())

    elif current_state == AppealState.waiting_for_contact_link.state:
        await state.set_state(AppealState.waiting_for_phone)
        await message.answer(
            "Укажите ваш номер телефона:", reply_markup=get_navigation_kb()
        )


# --- 7. ХЭНДЛЕРЫ ШАГОВ ---


@router.message(CommandStart())
@router.message(F.text.in_({"Начать", "Привет", "Предложалоба"}))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AppealState.waiting_for_type)
    await message.answer(
        "Добро пожаловать в модуль 'Предложалоба'.\nВыберите тип обращения:",
        reply_markup=get_type_kb(),
    )


@router.message(AppealState.waiting_for_type)
async def type_handler(message: Message, state: FSMContext):
    if message.text == AppealType.COMPLAINT.value:
        await state.update_data(type=AppealType.COMPLAINT.value)
        await state.set_state(AppealState.waiting_for_location)
        await message.answer(
            "Выберите локацию проблемы:", reply_markup=get_location_kb()
        )
    elif message.text == AppealType.SUGGESTION.value:
        await state.update_data(type=AppealType.SUGGESTION.value)
        await state.set_state(AppealState.waiting_for_description)
        await message.answer(
            "Опишите ваше предложение:", reply_markup=get_navigation_kb()
        )
    else:
        await message.answer(
            "Пожалуйста, воспользуйтесь кнопками.", reply_markup=get_type_kb()
        )


@router.message(AppealState.waiting_for_location)
async def location_handler(message: Message, state: FSMContext):
    try:
        loc = LocationType(message.text)
        await state.update_data(campus_location=loc.value)
        await state.set_state(AppealState.waiting_for_category)
        await message.answer(
            "Выберите категорию проблемы:", reply_markup=get_category_kb()
        )
    except ValueError:
        await message.answer(
            "Выберите локацию из списка.", reply_markup=get_location_kb()
        )


@router.message(AppealState.waiting_for_category)
async def category_handler(message: Message, state: FSMContext):
    try:
        cat = ProblemCategory(message.text)
        await state.update_data(problem_category=cat.value)
        await state.set_state(AppealState.waiting_for_timeframe)
        await message.answer(
            "Укажите ориентировочные сроки:", reply_markup=get_timeframe_kb()
        )
    except ValueError:
        await message.answer(
            "Выберите категорию из списка.", reply_markup=get_category_kb()
        )


@router.message(AppealState.waiting_for_timeframe)
async def timeframe_handler(message: Message, state: FSMContext):
    valid_timeframes = ["В течение дня", "До 3 дней", "В течение недели", "Не срочно"]
    if message.text not in valid_timeframes:
        await message.answer(
            "Пожалуйста, воспользуйтесь кнопками.", reply_markup=get_timeframe_kb()
        )
        return
    await state.update_data(timeframe=message.text)
    await state.set_state(AppealState.waiting_for_description)
    await message.answer(
        "Опишите суть вашей проблемы подробно:", reply_markup=get_navigation_kb()
    )


@router.message(AppealState.waiting_for_description)
async def description_handler(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AppealState.waiting_for_consent)
    consent_text = (
        "Даете ли вы согласие на обработку персональных данных?\n\n"
        "Ознакомиться с политикой можно по ссылке: https://example.com/privacy-policy"
    )
    await message.answer(consent_text, reply_markup=get_consent_kb())


@router.message(AppealState.waiting_for_consent)
async def consent_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text.lower() == "согласен":
        await state.update_data(personal_data_consent=True)
        await state.set_state(AppealState.waiting_for_name)
        await message.answer("Укажите ваши ФИО:", reply_markup=get_navigation_kb())
    elif message.text.lower() == "не согласен":
        if data.get("type") == AppealType.SUGGESTION.value:
            appeal = Appeal(
                type=AppealType(data.get("type")),
                description=data.get("description"),
                personal_data_consent=False,
                timeframe=data.get("timeframe"),
                tg_user_id=message.from_user.id,
            )
            await save_appeal_to_db(appeal)
            await state.clear()
            await message.answer(
                "✅ Ваше предложение отправлено анонимно.", reply_markup=get_start_kb()
            )
        else:
            await state.clear()
            await message.answer(
                "❌ Без согласия нельзя принять жалобу.", reply_markup=get_start_kb()
            )
    else:
        await message.answer(
            "Пожалуйста, воспользуйтесь кнопками.", reply_markup=get_consent_kb()
        )


@router.message(AppealState.waiting_for_name)
async def name_handler(message: Message, state: FSMContext):
    if not is_valid_name(message.text):
        await message.answer("⚠️ Некорректные ФИО. Введите, пожалуйста, снова:")
        return
    await state.update_data(contact_name=message.text)
    await state.set_state(AppealState.waiting_for_phone)
    await message.answer(
        "Укажите ваш номер телефона (Например: +79991234567):",
        reply_markup=get_navigation_kb(),
    )


@router.message(AppealState.waiting_for_phone)
async def phone_handler(message: Message, state: FSMContext):
    if not is_valid_phone(message.text):
        await message.answer("⚠️ Неверный формат телефона. Введите, пожалуйста, снова:")
        return
    await state.update_data(contact_phone=message.text)
    await state.set_state(AppealState.waiting_for_contact_link)
    await message.answer(
        "Укажите ваш E-mail, ссылку на страницу ВК или юзернейм Telegram:",
        reply_markup=get_navigation_kb(),
    )


@router.message(AppealState.waiting_for_contact_link)
async def contact_link_handler(message: Message, state: FSMContext):
    if not is_valid_contact_link(message.text):
        await message.answer("⚠️ Неверный формат. Укажите, пожалуйста, снова:")
        return

    data = await state.get_data()
    appeal = Appeal(
        type=AppealType(data.get("type")),
        campus_location=LocationType(
            data.get("campus_location", LocationType.NOT_APPLICABLE.value)
        ),
        problem_category=ProblemCategory(
            data.get("problem_category", ProblemCategory.NOT_APPLICABLE.value)
        ),
        timeframe=data.get("timeframe"),
        description=data.get("description"),
        contact_name=data.get("contact_name"),
        contact_phone=data.get("contact_phone"),
        contact_email=message.text,
        personal_data_consent=True,
        tg_user_id=message.from_user.id,
    )

    await save_appeal_to_db(appeal)
    await state.clear()
    await message.answer(
        "✅ Ваше обращение успешно зарегистрировано!", reply_markup=get_start_kb()
    )


# --- 8. РЕЗЕРВНЫЙ ХЭНДЛЕР ---


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "Пожалуйста, следуйте инструкциям или используйте кнопки «Назад» / «Отмена»."
        )
    else:
        await message.answer(
            "Я бот приема обращений. Для создания нового обращения нажмите «Начать».",
            reply_markup=get_start_kb(),
        )


async def main():
    logging.info("Бот 'Предложалоба' запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
