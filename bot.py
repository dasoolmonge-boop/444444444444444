#!/usr/bin/env python3
# bot.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ (бот + запуск мини-приложения)

import asyncio
import logging
import re
import sqlite3
import os
import sys
import subprocess
import threading
import time
import signal
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, CallbackQuery,
    WebAppInfo
)
from db_cakes import (
    init_db, get_available_cakes, get_cake_info,
    add_cake, update_cake, delete_cake,
    get_all_cakes_for_admin, create_order,
    get_active_orders, get_completed_orders, complete_order,
    get_cakes_by_ids, get_cake, cancel_order,
    get_cancelled_orders, mark_cake_as_available
)

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Для Windows исправляем кодировку
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass

# ============================================
# НАСТРОЙКИ БОТА
# ============================================

TOKEN = "8714739961:AAG9l-7-G7duRNKuNtarP7rTchfvZQFCMxo"
ADMIN_ID = 1066867845
MINI_APP_URL = "https://cake-shop.bothost.ru"  # ИСПРАВЛЕНО: добавлен https://

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

DB_NAME = "cake_shop.db"


# ============================================
# СОСТОЯНИЯ (FSM)
# ============================================

class AddCake(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name_price = State()
    waiting_for_description = State()
    waiting_for_weight = State()


class EditCake(StatesGroup):
    choosing_cake = State()
    choosing_field = State()
    waiting_for_new_name = State()
    waiting_for_new_price = State()
    waiting_for_new_description = State()
    waiting_for_new_weight = State()
    waiting_for_new_photo = State()


class DeleteCake(StatesGroup):
    confirming = State()


class OrderStates(StatesGroup):
    in_cart = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_delivery_date = State()
    waiting_for_delivery_time = State()
    waiting_for_wish = State()


# ============================================
# КЛАВИАТУРЫ
# ============================================

def get_user_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎂 Наши торты"), KeyboardButton(text="🛒 Корзина")],
            [KeyboardButton(text="🍰 Открыть каталог"), KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="ℹ️ О нас"), KeyboardButton(text="⭐ Акции")]
        ],
        resize_keyboard=True
    )


def get_admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎂 Наши торты"), KeyboardButton(text="🛒 Корзина")],
            [KeyboardButton(text="🍰 Открыть каталог"), KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="ℹ️ О нас"), KeyboardButton(text="⚙️ Админ-панель")]
        ],
        resize_keyboard=True
    )


def get_admin_panel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить торт"), KeyboardButton(text="✏️ Редактировать торт")],
            [KeyboardButton(text="🗑 Удалить торт"), KeyboardButton(text="📋 Активные заказы")],
            [KeyboardButton(text="✅ Выполненные заказы"), KeyboardButton(text="❌ Отмененные заказы")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )


def get_cart_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🔄 Обновить корзину", callback_data="refresh_cart")],
            [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")]
        ]
    )


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def validate_phone(phone: str) -> bool:
    pattern = r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
    return re.match(pattern, phone) is not None


# ============================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🍰 Добро пожаловать в «Сладкий рай»!\n\n"
        "Мы готовим самые вкусные торты в Кызыле 🎂\n"
        "Индивидуальный подход к каждому заказу ✨\n\n"
        "Нажмите «🍰 Открыть каталог» для просмотра тортов в удобном мини-приложении!"
    )
    if is_admin(message.from_user.id):
        await message.answer(
            f"{welcome_text}\n\nВы вошли как администратор.",
            reply_markup=get_admin_main_keyboard()
        )
    else:
        await message.answer(
            welcome_text,
            reply_markup=get_user_main_keyboard()
        )


@dp.message(F.text == "🍰 Открыть каталог")
async def open_mini_app(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🍰 Открыть каталог тортов",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]]
    )

    await message.answer(
        "🍰 Нажмите кнопку ниже, чтобы открыть каталог тортов в мини-приложении:",
        reply_markup=keyboard
    )


@dp.message(F.text == "🔙 Назад в меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = get_admin_main_keyboard() if is_admin(message.from_user.id) else get_user_main_keyboard()
    await message.answer("🍰 Вы в главном меню", reply_markup=keyboard)


@dp.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("⚙️ Панель администратора", reply_markup=get_admin_panel_keyboard())


@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: types.Message):
    contacts_text = (
        "📞 **Наши контакты:**\n\n"
        "📍 **Адрес:** г. Кызыл, ул. Кочетова, 25\n"
        "📱 **Телефон:** +7 (923) 456-78-90\n"
        "📧 **Email:** cakes@kyzyl.ru\n"
        "🕒 **Режим работы:** 10:00 - 20:00 ежедневно"
    )
    await message.answer(contacts_text, parse_mode="Markdown")


@dp.message(F.text == "ℹ️ О нас")
async def show_about(message: types.Message):
    about_text = (
        "🍰 **О нашей кондитерской**\n\n"
        "«Сладкий рай» — это домашняя кондитерская с душой ❤️\n\n"
        "✨ Почему выбирают нас:\n"
        "• Только натуральные ингредиенты\n"
        "• Ручная работа\n"
        "• Уникальные рецепты\n"
        "• Индивидуальный дизайн\n"
        "• Бесплатная доставка от 3000₽"
    )
    await message.answer(about_text, parse_mode="Markdown")


@dp.message(F.text == "⭐ Акции")
async def show_promos(message: types.Message):
    promos_text = (
        "⭐ **Наши акции:**\n\n"
        "🎁 **При заказе от 3000₽** - бесплатная доставка\n"
        "🎂 **Именинникам** - скидка 10%\n"
        "🔄 **При повторном заказе** - скидка 5%"
    )
    await message.answer(promos_text, parse_mode="Markdown")


@dp.message(F.text == "🎂 Наши торты")
async def show_cakes(message: types.Message, state: FSMContext):
    cakes = await get_available_cakes()
    if not cakes:
        await message.answer("🍰 Скоро здесь появятся наши вкуснейшие торты!")
        return

    await message.answer("🍰 **Наши торты:**", parse_mode="Markdown")

    for cake in cakes:
        cake_id, name, price, weight, description, photo_id = cake
        buttons = [[
            InlineKeyboardButton(
                text="🛒 Добавить в корзину",
                callback_data=f"add_to_cart:{cake_id}"
            )
        ]]

        caption = (
            f"🍰 *{name}*\n"
            f"💰 *{price} ₽*  |  ⚖️ *{weight} кг*\n\n"
            f"_{description}_"
        )

        await message.answer_photo(
            photo=photo_id,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@dp.message(F.text == "🛒 Корзина")
async def show_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get('cart', [])

    if not cart:
        await message.answer("🛒 Ваша корзина пуста")
        return

    cart_text = "🛒 **Ваша корзина:**\n\n"
    total_price = 0
    keyboard = []

    for item in cart:
        cake = await get_cake(item['cake_id'])
        if cake:
            name, price, weight = cake[1], cake[2], cake[3]
            cart_text += f"🍰 {name} - {price} ₽ ({weight} кг)\n"
            total_price += price
            keyboard.append([
                InlineKeyboardButton(
                    text=f"❌ Удалить {name[:20]}",
                    callback_data=f"remove_from_cart:{item['cake_id']}"
                )
            ])

    cart_text += f"\n💰 **Итого: {total_price} ₽**"

    keyboard.append([InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_cart")])
    keyboard.append([InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")])

    await message.answer(
        cart_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@dp.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    cake_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    cart = data.get('cart', [])
    cart.append({'cake_id': cake_id})
    await state.update_data(cart=cart)
    await callback.answer("✅ Торт добавлен в корзину!")
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ В корзине",
                callback_data=f"already_in_cart:{cake_id}"
            )]
        ])
    )


@dp.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: CallbackQuery, state: FSMContext):
    cake_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    cart = data.get('cart', [])

    for i, item in enumerate(cart):
        if item['cake_id'] == cake_id:
            cart.pop(i)
            break

    await state.update_data(cart=cart)
    await callback.answer("❌ Торт удалён из корзины")
    await callback.message.delete()
    await show_cart(callback.message, state)


@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cart=[])
    await callback.answer("🧹 Корзина очищена")
    await callback.message.delete()
    await show_cart(callback.message, state)


@dp.callback_query(F.data == "refresh_cart")
async def refresh_cart(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    await show_cart(callback.message, state)


@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get('cart', [])

    if not cart:
        await callback.answer("❌ Корзина пуста!")
        return

    await callback.message.delete()
    await callback.message.answer(
        "📝 **Оформление заказа**\n\n"
        "Шаг 1 из 5:\n"
        "Введите ваше **имя**:",
        parse_mode="Markdown"
    )
    await state.set_state(OrderStates.waiting_for_name)
    await callback.answer()


@dp.message(OrderStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("❌ Имя должно содержать хотя бы 2 символа. Попробуйте ещё раз:")
        return

    await state.update_data(customer_name=message.text.strip())
    await message.answer(
        "Шаг 2 из 5:\n"
        "Введите ваш **номер телефона**:\n\n"
        "Пример: +7 923 456-78-90 или 89234567890"
    )
    await state.set_state(OrderStates.waiting_for_phone)


@dp.message(OrderStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()

    if not validate_phone(phone):
        await message.answer(
            "❌ Неверный формат телефона.\n"
            "Пример: +7 923 456-78-90 или 89234567890\n\n"
            "Попробуйте ещё раз:"
        )
        return

    await state.update_data(customer_phone=phone)
    await message.answer(
        "Шаг 3 из 5:\n"
        "Введите **адрес доставки**:\n\n"
        "Пример: ул. Кочетова, д. 25, кв. 42"
    )
    await state.set_state(OrderStates.waiting_for_address)


@dp.message(OrderStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("❌ Укажите корректный адрес. Попробуйте ещё раз:")
        return

    await state.update_data(address=message.text.strip())
    await message.answer(
        "Шаг 4 из 5:\n"
        "Введите **дату доставки**:\n\n"
        "Пример: 25.12.2024 или завтра/послезавтра"
    )
    await state.set_state(OrderStates.waiting_for_delivery_date)


@dp.message(OrderStates.waiting_for_delivery_date)
async def process_delivery_date(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        await message.answer("❌ Укажите корректную дату. Попробуйте ещё раз:")
        return

    await state.update_data(delivery_date=message.text.strip())
    await message.answer(
        "Шаг 5 из 5:\n"
        "Введите **время доставки**:\n\n"
        "Пример: 14:00 или с 15:00 до 17:00"
    )
    await state.set_state(OrderStates.waiting_for_delivery_time)


@dp.message(OrderStates.waiting_for_delivery_time)
async def process_delivery_time(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        await message.answer("❌ Укажите корректное время. Попробуйте ещё раз:")
        return

    await state.update_data(delivery_time=message.text.strip())
    await message.answer(
        "Последний шаг:\n"
        "Напишите **пожелания к торту**:\n\n"
        "(надпись, декор, особые пожелания)\n"
        "Если пожеланий нет, отправьте \"Нет\""
    )
    await state.set_state(OrderStates.waiting_for_wish)


@dp.message(OrderStates.waiting_for_wish)
async def process_wish(message: types.Message, state: FSMContext):
    wish = message.text.strip() if message.text.strip().lower() != "нет" else "Без пожеланий"
    data = await state.get_data()

    cart = data.get('cart', [])
    name = data.get('customer_name')
    phone = data.get('customer_phone')
    address = data.get('address')
    delivery_date = data.get('delivery_date')
    delivery_time = data.get('delivery_time')

    if not cart:
        await message.answer("❌ Корзина пуста. Заказ не может быть оформлен.")
        await state.clear()
        return

    cakes_info = []
    total_price = 0

    for item in cart:
        cake = await get_cake(item['cake_id'])
        if cake and cake[6] == 1:
            cakes_info.append(cake)
            delivery_info = f"Дата: {delivery_date}, Время: {delivery_time}, Адрес: {address}"
            await create_order(item['cake_id'], name, phone, delivery_info, wish)
            total_price += cake[2]

    if not cakes_info:
        await message.answer("❌ Некоторые торты из корзины уже недоступны.")
        await state.clear()
        return

    cakes_list = "\n".join([f"🍰 {c[1]} - {c[2]} ₽ ({c[3]} кг)" for c in cakes_info])
    admin_message = (
        f"📩 **НОВЫЙ ЗАКАЗ**\n\n"
        f"🍰 **Торты:**\n{cakes_list}\n"
        f"💰 **Итого:** {total_price} ₽\n\n"
        f"👤 **Имя:** {name}\n"
        f"📱 **Телефон:** {phone}\n"
        f"📍 **Адрес:** {address}\n"
        f"📅 **Доставка:** {delivery_date} в {delivery_time}\n"
        f"📝 **Пожелания:** {wish}"
    )

    await bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")

    await message.answer(
        f"✅ **Заказ успешно оформлен!**\n\n"
        f"Спасибо, {name}! 🍰\n"
        f"Мы скоро свяжемся с вами.\n\n"
        f"🍰 Ваш заказ:\n{cakes_list}\n\n"
        f"📍 Адрес: {address}\n"
        f"📅 Доставка: {delivery_date} в {delivery_time}\n"
        f"💰 Сумма: {total_price} ₽",
        parse_mode="Markdown",
        reply_markup=get_user_main_keyboard() if not is_admin(message.from_user.id) else get_admin_main_keyboard()
    )

    await state.clear()


# ============================================
# АДМИН-ФУНКЦИИ (добавление, редактирование, удаление)
# ============================================

@dp.message(F.text == "➕ Добавить торт")
async def add_cake_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📸 Отправьте фото торта",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddCake.waiting_for_photo)


@dp.message(AddCake.waiting_for_photo, F.photo)
async def add_cake_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer(
        "🍰 Введите название и цену торта через запятую\n"
        "Пример: **Медовик, 2500**"
    )
    await state.set_state(AddCake.waiting_for_name_price)


@dp.message(AddCake.waiting_for_name_price)
async def add_cake_name_price(message: types.Message, state: FSMContext):
    try:
        if "," not in message.text:
            raise ValueError("Отсутствует запятая")

        name, price_str = map(str.strip, message.text.split(",", 1))
        price = int(price_str)

        if price <= 0:
            raise ValueError("Цена должна быть положительной")

    except ValueError:
        await message.answer(
            "❌ Неверный формат.\n"
            "Используйте: **название, цена**\n"
            "Пример: **Медовик, 2500**"
        )
        return

    await state.update_data(name=name, price=price)
    await message.answer("⚖️ Укажите вес торта (в кг):\nПример: 1.5, 2, 2.5")
    await state.set_state(AddCake.waiting_for_weight)


@dp.message(AddCake.waiting_for_weight)
async def add_cake_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.strip().replace(',', '.'))
        if weight <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректный вес (например: 1.5, 2, 2.5)")
        return

    await state.update_data(weight=weight)
    await message.answer("📝 Введите описание торта:\n(Состав, особенности, начинка)")
    await state.set_state(AddCake.waiting_for_description)


@dp.message(AddCake.waiting_for_description)
async def add_cake_description(message: types.Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("❌ Описание слишком короткое. Напишите хотя бы 10 символов.")
        return

    data = await state.get_data()
    await add_cake(data["name"], data["price"], data["weight"], message.text, data["photo_id"])

    await message.answer(
        "✅ Торт успешно добавлен в меню!",
        reply_markup=get_admin_panel_keyboard()
    )
    await state.clear()


# ============================================
# ЗАПУСК МИНИ-ПРИЛОЖЕНИЯ (Node.js)
# ============================================

processes = []


def cleanup(signum=None, frame=None):
    """Очистка процессов при завершении"""
    logger.info("Завершение работы...")
    for proc in processes:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                logger.info(f"Процесс {proc.pid} завершен")
            except:
                pass
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def start_mini_app():
    """Запуск мини-приложения в фоновом режиме"""
    try:
        root_dir = Path(__file__).parent

        # Поиск папки с мини-приложением
        possible_paths = [
            root_dir / "telegram-cake-miniapp",
            root_dir / "Крутой тортик" / "telegram-cake-miniapp",
        ]

        mini_app_path = None
        for path in possible_paths:
            if path.exists() and (path / "package.json").exists():
                mini_app_path = path
                break

        if not mini_app_path:
            logger.warning("⚠️ Папка с мини-приложением не найдена")
            return None

        logger.info(f"📁 Мини-приложение найдено: {mini_app_path}")

        # Переходим в папку мини-приложения
        os.chdir(mini_app_path)

        # Проверяем наличие package.json
        if not Path("package.json").exists():
            logger.error("❌ package.json не найден")
            return None

        # Устанавливаем зависимости если нужно
        if not Path("node_modules").exists():
            logger.info("📦 Установка зависимостей мини-приложения...")
            npm_install = subprocess.run(
                ["npm", "install"],
                capture_output=True,
                text=True
            )
            if npm_install.returncode != 0:
                logger.error(f"❌ Ошибка установки зависимостей: {npm_install.stderr}")
                return None
            logger.info("✅ Зависимости установлены")

        # Запускаем сервер
        logger.info("🌐 Запуск мини-приложения...")
        proc = subprocess.Popen(
            ["npm", "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='ignore'
        )

        processes.append(proc)

        # Поток для вывода логов мини-приложения
        def log_output():
            for line in proc.stdout:
                if line:
                    logger.info(f"[MINI-APP] {line.strip()}")

        threading.Thread(target=log_output, daemon=True).start()
        logger.info(f"✅ Мини-приложение запущено (PID: {proc.pid})")
        return proc

    except Exception as e:
        logger.error(f"❌ Ошибка запуска мини-приложения: {e}")
        return None


# ============================================
# ОСНОВНАЯ ФУНКЦИЯ БОТА
# ============================================

async def bot_main():
    """Главная функция запуска бота"""
    try:
        logger.info("=" * 50)
        logger.info("🍰 ЗАПУСК TELEGRAM БОТА")
        logger.info("=" * 50)

        # Инициализация БД
        logger.info("Инициализация базы данных...")
        await init_db()
        logger.info("✅ База данных инициализирована")

        # Удаление вебхука
        logger.info("Удаление вебхука...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Вебхук удален")

        # Запуск бота
        logger.info("🚀 Запуск бота...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")
        import traceback
        traceback.print_exc()


# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🍰 ЗАПУСК БОТА И МИНИ-ПРИЛОЖЕНИЯ")
    print("=" * 60 + "\n")

    print(f"📋 Информация о запуске:")
    print(f"   • Токен: {TOKEN[:10]}...")
    print(f"   • Admin ID: {ADMIN_ID}")
    print(f"   • Mini App URL: {MINI_APP_URL}")
    print(f"   • Python: {sys.version}")
    print()

    # 1. ЗАПУСКАЕМ МИНИ-ПРИЛОЖЕНИЕ В ФОНЕ
    print("🔄 Запуск мини-приложения...")
    mini_app = start_mini_app()
    time.sleep(2)

    # 2. ЗАПУСКАЕМ БОТА (ОН ЗАБЛОКИРУЕТ ОСНОВНОЙ ПОТОК)
    print("🔄 Запуск Telegram бота...")

    try:
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        if mini_app:
            mini_app.terminate()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        if mini_app:
            mini_app.terminate()

    print("🏁 Программа завершена")