import os
import shutil

def create_folder_structure():
    folders = [
        "database",
        "handlers",
        "keyboards",
        "utils"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        
    print("✅ Folder structure created successfully!")

def create_files():
    files = {
        "main.py": """import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.setup import create_tables
from handlers import register_all_handlers

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
    dp = Dispatcher(storage=MemoryStorage())
    
    register_all_handlers(dp)
    
    await create_tables()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())""",
        
        "config.py": """BOT_TOKEN = "8019368456:AAE7ygorqGcZaj71-sp749AVWjEn0e2pM9M"
ADMIN_ID = 6236467772
DATABASE_URL = "postgresql://taxi_bot_user:UolYceT8tfkaShOFGZhQbHWo4ePVebIG@dpg-cvie39ogjchc73cscr80-a.oregon-postgres.render.com/taxi_bot"
DRIVERS_GROUP_ID = None""",
        
        "database/setup.py": """import asyncpg
from config import DATABASE_URL

async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            phone_number TEXT,
            role TEXT,
            is_banned BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
            car_name TEXT,
            seats_count INTEGER,
            car_photo TEXT,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            passenger_id BIGINT REFERENCES users(user_id),
            direction TEXT,
            passengers_count INTEGER,
            is_pochta BOOLEAN DEFAULT FALSE,
            note TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
            added_by BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await conn.execute('''
        INSERT INTO admins (user_id, added_by)
        VALUES ($1, $1)
        ON CONFLICT (user_id) DO NOTHING
    ''', int(6236467772))
    
    await conn.close()""",
        
        "database/operations.py": """import asyncpg
from config import DATABASE_URL

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

async def add_user(user_id, full_name, username):
    conn = await get_connection()
    await conn.execute('''
        INSERT INTO users (user_id, full_name, username)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO NOTHING
    ''', user_id, full_name, username)
    await conn.close()

async def update_user_role(user_id, role):
    conn = await get_connection()
    await conn.execute('''
        UPDATE users SET role = $1 WHERE user_id = $2
    ''', role, user_id)
    await conn.close()

async def update_user_phone(user_id, phone_number):
    conn = await get_connection()
    await conn.execute('''
        UPDATE users SET phone_number = $1 WHERE user_id = $2
    ''', phone_number, user_id)
    await conn.close()

async def get_user(user_id):
    conn = await get_connection()
    user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
    await conn.close()
    return user

async def get_all_users():
    conn = await get_connection()
    users = await conn.fetch('SELECT * FROM users')
    await conn.close()
    return users

async def ban_user(user_id, ban_status=True):
    conn = await get_connection()
    await conn.execute('''
        UPDATE users SET is_banned = $1 WHERE user_id = $2
    ''', ban_status, user_id)
    await conn.close()

async def add_driver(user_id, car_name, seats_count, car_photo):
    conn = await get_connection()
    await conn.execute('''
        INSERT INTO drivers (user_id, car_name, seats_count, car_photo)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO UPDATE SET
        car_name = $2, seats_count = $3, car_photo = $4
    ''', user_id, car_name, seats_count, car_photo)
    await conn.close()

async def get_all_drivers():
    conn = await get_connection()
    drivers = await conn.fetch('''
        SELECT u.user_id, u.full_name, u.phone_number, u.is_banned,
               d.car_name, d.seats_count, d.is_active
        FROM users u
        JOIN drivers d ON u.user_id = d.user_id
    ''')
    await conn.close()
    return drivers

async def toggle_driver_status(user_id, is_active):
    conn = await get_connection()
    await conn.execute('''
        UPDATE drivers SET is_active = $1 WHERE user_id = $2
    ''', is_active, user_id)
    await conn.close()

async def create_order(passenger_id, direction, passengers_count, is_pochta, note):
    conn = await get_connection()
    order_id = await conn.fetchval('''
        INSERT INTO orders (passenger_id, direction, passengers_count, is_pochta, note)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
    ''', passenger_id, direction, passengers_count, is_pochta, note)
    await conn.close()
    return order_id

async def get_order(order_id):
    conn = await get_connection()
    order = await conn.fetchrow('''
        SELECT o.*, u.full_name, u.phone_number
        FROM orders o
        JOIN users u ON o.passenger_id = u.user_id
        WHERE o.id = $1
    ''', order_id)
    await conn.close()
    return order

async def get_active_orders():
    conn = await get_connection()
    orders = await conn.fetch('''
        SELECT o.*, u.full_name, u.phone_number
        FROM orders o
        JOIN users u ON o.passenger_id = u.user_id
        WHERE o.status = 'active'
        ORDER BY o.created_at DESC
    ''')
    await conn.close()
    return orders

async def is_admin(user_id):
    conn = await get_connection()
    admin = await conn.fetchval('SELECT user_id FROM admins WHERE user_id = $1', user_id)
    await conn.close()
    return admin is not None

async def add_admin(user_id, added_by):
    conn = await get_connection()
    await conn.execute('''
        INSERT INTO admins (user_id, added_by)
        VALUES ($1, $2)
        ON CONFLICT (user_id) DO NOTHING
    ''', user_id, added_by)
    await conn.close()

async def get_all_admins():
    conn = await get_connection()
    admins = await conn.fetch('''
        SELECT a.user_id, u.full_name, u.username, a.created_at
        FROM admins a
        JOIN users u ON a.user_id = u.user_id
    ''')
    await conn.close()
    return admins

async def get_statistics():
    conn = await get_connection()
    
    total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
    total_drivers = await conn.fetchval('SELECT COUNT(*) FROM drivers')
    active_drivers = await conn.fetchval('SELECT COUNT(*) FROM drivers WHERE is_active = TRUE')
    total_orders = await conn.fetchval('SELECT COUNT(*) FROM orders')
    active_orders = await conn.fetchval('SELECT COUNT(*) FROM orders WHERE status = \'active\'')
    
    await conn.close()
    
    return {
        "total_users": total_users,
        "total_drivers": total_drivers,
        "active_drivers": active_drivers,
        "total_orders": total_orders,
        "active_orders": active_orders
    }""",
        
        "database/__init__.py": "",
        
        "utils/states.py": """from aiogram.fsm.state import State, StatesGroup

class UserRole(StatesGroup):
    choosing_role = State()

class DriverRegistration(StatesGroup):
    car_name = State()
    seats_count = State()
    full_name = State()
    phone_number = State()
    car_photo = State()

class PassengerOrder(StatesGroup):
    direction = State()
    full_name = State()
    passengers_count = State()
    phone_number = State()
    note = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_broadcast_message = State()
    waiting_for_admin_id = State()
    waiting_for_group_id = State()""",
        
        "utils/text_messages.py": """WELCOME_MESSAGE = "🚕 *Taxi xizmatiga xush kelibsiz\\!*\n\n🔍 Ro'lni tanlang:"
ROLE_SELECTION = "Siz kimman?"

DRIVER_WELCOME = "👋 *Haydovchi sifatida xush kelibsiz\\!*\n\n🚗 Ro'yxatdan o'tish uchun quyidagi ma'lumotlarni kiriting:"
DRIVER_CAR_NAME = "🚗 Avtomobil nomini kiriting:"
DRIVER_SEATS_COUNT = "👥 Avtomobilizda nechta o'rindiq bor?"
DRIVER_FULL_NAME = "👤 To'liq ismingizni kiriting:"
DRIVER_PHONE_NUMBER = "📱 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing:"
DRIVER_CAR_PHOTO = "📷 Avtomobilingizni rasmini yuboring:"
DRIVER_REGISTRATION_COMPLETE = "✅ *Ro'yxatdan o'tish muvaffaqiyatli yakunlandi\\!*\n\n🔔 Yangi buyurtmalar haqida xabardor qilinasiz\\.\n\n🚦 Holatni tanlang:"
DRIVER_MENU = "🚕 *Haydovchi menyusi*\n\n🚦 Holatni tanlang:"

PASSENGER_WELCOME = "👋 *Yo'lovchi sifatida xush kelibsiz\\!*\n\n🧭 Qayerga bormoqchisiz?"
PASSENGER_DIRECTION = "🧭 Qaysi yo'nalishda ketmoqchisiz?"
PASSENGER_FULL_NAME = "👤 To'liq ismingizni kiriting:"
PASSENGER_COUNT = "👥 Nechta yo'lovchi bor yoki pochta yubormoqchimisiz?"
PASSENGER_PHONE_NUMBER = "📱 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing:"
PASSENGER_NOTE = "📝 Haydovchi uchun qo'shimcha ma'lumot kiriting \$$ixtiyoriy\$$:"
PASSENGER_ORDER_COMPLETE = "✅ *Buyurtmangiz qabul qilindi\\!*\n\n⏳ Haydovchilar tez orada siz bilan bog'lanishadi\\.\n\n🙏 Xizmatimizdan foydalanganingiz uchun rahmat\\!"

ADMIN_WELCOME = "👑 *Admin paneliga xush kelibsiz\\!*\n\n⚙️ Quyidagi amallardan birini tanlang:"
ADMIN_STATS = "📊 *Statistika*\n\n👥 Foydalanuvchilar: {total_users}\n🚕 Haydovchilar: {total_drivers}\n✅ Faol haydovchilar: {active_drivers}\n📋 Jami buyurtmalar: {total_orders}\n🔄 Faol buyurtmalar: {active_orders}"
ADMIN_BROADCAST_PROMPT = "📣 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabarni kiriting:"
ADMIN_BROADCAST_SENT = "✅ Xabar {count} ta foydalanuvchiga yuborildi."
ADMIN_ADD_ADMIN_PROMPT = "👑 Yangi admin ID raqamini kiriting:"
ADMIN_ADDED = "✅ Yangi admin qo'shildi."
ADMIN_SET_GROUP_PROMPT = "👥 Haydovchilar guruhi ID raqamini kiriting:"
ADMIN_GROUP_SET = "✅ Haydovchilar guruhi sozlandi."

NEW_ORDER_NOTIFICATION = "🔔 *Yangi buyurtma\\!*\n\n🧭 Yo'nalish: {direction}\n👥 Yo'lovchilar soni: {passengers_count}\n📝 Izoh: {note}\n\n🔍 Batafsil ma'lumot uchun haydovchilar guruhiga qarang\\."
NEW_ORDER_GROUP = "🔔 *Yangi buyurtma\\!*\n\n👤 Yo'lovchi: {full_name}\n🧭 Yo'nalish: {direction}\n👥 Yo'lovchilar soni: {passengers_count}\n📱 Telefon: {phone_number}\n📝 Izoh: {note}"

BTN_DRIVER = "🚕 Haydovchi"
BTN_PASSENGER = "👤 Yo'lovchi"
BTN_TASHKENT_TO_SAMARKAND = "🏙️ Toshkent ➡️ Samarqand"
BTN_SAMARKAND_TO_TASHKENT = "🏛️ Samarqand ➡️ Toshkent"
BTN_SEND_PHONE = "📱 Telefon raqamni yuborish"
BTN_POCHTA = "📦 Pochta"
BTN_BACK = "🔙 Orqaga"
BTN_CANCEL = "❌ Bekor qilish"
BTN_MENU = "📋 Menyu"

BTN_ADMIN_STATS = "📊 Statistika"
BTN_ADMIN_DRIVERS = "🚕 Haydovchilar ro'yxati"
BTN_ADMIN_BROADCAST = "📣 Xabar yuborish"
BTN_ADMIN_ADD_ADMIN = "👑 Admin qo'shish"
BTN_ADMIN_SET_GROUP = "👥 Guruh sozlash"
BTN_ADMIN_BAN_USER = "🚫 Bloklash"
BTN_ADMIN_UNBAN_USER = "✅ Blokdan chiqarish"
BTN_ADMIN_ORDERS = "📋 Buyurtmalar"

BTN_DRIVER_ACTIVE = "✅ Faol"
BTN_DRIVER_INACTIVE = "❌ Faol emas"
""",
        
        "utils/__init__.py": "",
        
        "keyboards/reply.py": """from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.text_messages import *

def get_role_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_DRIVER),
                KeyboardButton(text=BTN_PASSENGER)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_SEND_PHONE, request_contact=True)
            ],
            [
                KeyboardButton(text=BTN_CANCEL)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_direction_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_TASHKENT_TO_SAMARKAND)
            ],
            [
                KeyboardButton(text=BTN_SAMARKAND_TO_TASHKENT)
            ],
            [
                KeyboardButton(text=BTN_CANCEL)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_passenger_count_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="1"),
                KeyboardButton(text="2"),
                KeyboardButton(text="3"),
            ],
            [
                KeyboardButton(text="4"),
                KeyboardButton(text="5"),
                KeyboardButton(text="6"),
            ],
            [
                KeyboardButton(text=BTN_POCHTA),
                KeyboardButton(text=BTN_CANCEL)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_CANCEL)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_driver_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_DRIVER_ACTIVE),
                KeyboardButton(text=BTN_DRIVER_INACTIVE)
            ],
            [
                KeyboardButton(text=BTN_MENU)
            ],
            [
                KeyboardButton(text=BTN_CANCEL)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_DRIVER),
                KeyboardButton(text=BTN_PASSENGER)
            ],
            [
                KeyboardButton(text=BTN_MENU)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard""",
        
        "keyboards/inline.py": """from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.text_messages import *

def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=BTN_ADMIN_STATS, callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text=BTN_ADMIN_DRIVERS, callback_data="admin_drivers"),
                InlineKeyboardButton(text=BTN_ADMIN_ORDERS, callback_data="admin_orders")
            ],
            [
                InlineKeyboardButton(text=BTN_ADMIN_BROADCAST, callback_data="admin_broadcast"),
                InlineKeyboardButton(text=BTN_ADMIN_SET_GROUP, callback_data="admin_set_group")
            ],
            [
                InlineKeyboardButton(text=BTN_ADMIN_ADD_ADMIN, callback_data="admin_add_admin")
            ]
        ]
    )
    return keyboard

def get_driver_action_keyboard(driver_id, is_banned):
    ban_text = BTN_ADMIN_UNBAN_USER if is_banned else BTN_ADMIN_BAN_USER
    ban_data = f"unban_{driver_id}" if is_banned else f"ban_{driver_id}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=ban_text, callback_data=ban_data)
            ],
            [
                InlineKeyboardButton(text=BTN_BACK, callback_data="admin_drivers")
            ]
        ]
    )
    return keyboard

def get_drivers_list_keyboard(drivers):
    keyboard = []
    
    for driver in drivers:
        status = "✅" if not driver["is_banned"] and driver["is_active"] else "❌"
        button_text = f"{status} {driver['full_name']} - {driver['car_name']}"
        keyboard.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"driver_{driver['user_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_orders_list_keyboard(orders):
    keyboard = []
    
    for order in orders:
        direction_emoji = "🏙️➡️🏛️" if "Toshkent➡️Samarqand" in order["direction"] else "🏛️➡️🏙️"
        button_text = f"{direction_emoji} {order['full_name']}"
        keyboard.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"order_{order['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_admin_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=BTN_BACK, callback_data="admin_menu")
            ]
        ]
    )
    return keyboard

def get_passenger_action_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=BTN_TASHKENT_TO_SAMARKAND, callback_data="direction_tashkent_samarkand")
            ],
            [
                InlineKeyboardButton(text=BTN_SAMARKAND_TO_TASHKENT, callback_data="direction_samarkand_tashkent")
            ]
        ]
    )
    return keyboard""",
        
        "keyboards/__init__.py": "",
        
        "handlers/__init__.py": """from aiogram import Dispatcher
from handlers.start import register_start_handlers
from handlers.driver import register_driver_handlers
from handlers.passenger import register_passenger_handlers
from handlers.admin import register_admin_handlers
from handlers.common import register_common_handlers

def register_all_handlers(dp: Dispatcher):
    handlers = [
        register_common_handlers,
        register_start_handlers,
        register_driver_handlers,
        register_passenger_handlers,
        register_admin_handlers,
    ]
    
    for handler in handlers:
        handler(dp)""",
        
        "handlers/start.py": """from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.states import UserRole
from utils.text_messages import WELCOME_MESSAGE
from keyboards.reply import get_role_keyboard
from database.operations import add_user, update_user_role

async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    await add_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username
    )
    
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_role_keyboard()
    )
    
    await state.set_state(UserRole.choosing_role)

async def process_role_selection(message: Message, state: FSMContext):
    from utils.text_messages import BTN_DRIVER, BTN_PASSENGER
    from handlers.driver import start_driver_registration
    from handlers.passenger import start_passenger_order
    
    if message.text == BTN_DRIVER:
        await update_user_role(message.from_user.id, "driver")
        await start_driver_registration(message, state)
    
    elif message.text == BTN_PASSENGER:
        await update_user_role(message.from_user.id, "passenger")
        await start_passenger_order(message, state)
    
    else:
        await message.answer(
            "Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=get_role_keyboard()
        )

async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    
    await message.answer(
        "📋 *Asosiy menyu*\n\nRo'lni tanlang:",
        reply_markup=get_role_keyboard()
    )

def register_start_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_menu, Command("menu"))
    dp.message.register(cmd_menu, F.text == "📋 Menyu")
    dp.message.register(process_role_selection, UserRole.choosing_role)""",
        
        "handlers/driver.py": """from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from utils.states import DriverRegistration
from utils.text_messages import *
from keyboards.reply import get_phone_keyboard, get_driver_menu_keyboard, get_cancel_keyboard
from database.operations import update_user_phone, add_driver, toggle_driver_status

async def start_driver_registration(message: Message, state: FSMContext):
    await message.answer(
        DRIVER_WELCOME,
        reply_markup=get_cancel_keyboard()
    )
    
    await message.answer(DRIVER_CAR_NAME)
    await state.set_state(DriverRegistration.car_name)

async def process_car_name(message: Message, state: FSMContext):
    await state.update_data(car_name=message.text)
    
    await message.answer(DRIVER_SEATS_COUNT)
    await state.set_state(DriverRegistration.seats_count)

async def process_seats_count(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Iltimos, to'g'ri raqam kiriting.")
        return
    
    await state.update_data(seats_count=int(message.text))
    
    await message.answer(DRIVER_FULL_NAME)
    await state.set_state(DriverRegistration.full_name)

async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    
    await message.answer(
        DRIVER_PHONE_NUMBER,
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(DriverRegistration.phone_number)

async def process_phone_number(message: Message, state: FSMContext):
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    await update_user_phone(message.from_user.id, phone)
    await state.update_data(phone_number=phone)
    
    await message.answer(
        DRIVER_CAR_PHOTO,
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(DriverRegistration.car_photo)

async def process_car_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Iltimos, avtomobil rasmini yuboring.")
        return
    
    photo = message.photo[-1]
    
    await state.update_data(car_photo=photo.file_id)
    
    data = await state.get_data()
    
    await add_driver(
        message.from_user.id,
        data["car_name"],
        data["seats_count"],
        data["car_photo"]
    )
    
    await message.answer(
        DRIVER_REGISTRATION_COMPLETE,
        reply_markup=get_driver_menu_keyboard()
    )
    
    await state.clear()

async def process_driver_status(message: Message, state: FSMContext):
    if message.text == BTN_DRIVER_ACTIVE:
        await toggle_driver_status(message.from_user.id, True)
        await message.answer("✅ Siz faol holatdasiz. Yangi buyurtmalar haqida xabardor qilinasiz.", reply_markup=get_driver_menu_keyboard())
    
    elif message.text == BTN_DRIVER_INACTIVE:
        await toggle_driver_status(message.from_user.id, False)
        await message.answer("❌ Siz faol emas holatidasiz. Yangi buyurtmalar haqida xabardor qilinmaysiz.", reply_markup=get_driver_menu_keyboard())

def register_driver_handlers(dp: Dispatcher):
    dp.message.register(process_car_name, DriverRegistration.car_name)
    dp.message.register(process_seats_count, DriverRegistration.seats_count)
    dp.message.register(process_full_name, DriverRegistration.full_name)
    dp.message.register(process_phone_number, DriverRegistration.phone_number, F.contact | F.text)
    dp.message.register(process_car_photo, DriverRegistration.car_photo, F.photo)
    dp.message.register(process_driver_status, F.text.in_([BTN_DRIVER_ACTIVE, BTN_DRIVER_INACTIVE]))""",
        
        "handlers/passenger.py": """from aiogram import Dispatcher, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import DRIVERS_GROUP_ID

from utils.states import PassengerOrder
from utils.text_messages import *
from keyboards.reply import (
    get_direction_keyboard, 
    get_passenger_count_keyboard, 
    get_phone_keyboard,
    get_cancel_keyboard,
    get_menu_keyboard
)
from keyboards.inline import get_passenger_action_keyboard
from database.operations import (
    update_user_phone, 
    create_order, 
    get_order,
    get_all_drivers
)

async def start_passenger_order(message: Message, state: FSMContext):
    await message.answer(
        PASSENGER_WELCOME,
        reply_markup=get_direction_keyboard()
    )
    
    await state.set_state(PassengerOrder.direction)

async def process_direction(message: Message, state: FSMContext):
    if message.text not in [BTN_TASHKENT_TO_SAMARKAND, BTN_SAMARKAND_TO_TASHKENT]:
        await message.answer(
            "❌ Iltimos, yo'nalishni tanlang:",
            reply_markup=get_direction_keyboard()
        )
        return
    
    direction = "Toshkent➡️Samarqand" if message.text == BTN_TASHKENT_TO_SAMARKAND else "Samarqand➡️Toshkent"
    await state.update_data(direction=direction)
    
    await message.answer(
        PASSENGER_FULL_NAME,
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PassengerOrder.full_name)

async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    
    await message.answer(
        PASSENGER_COUNT,
        reply_markup=get_passenger_count_keyboard()
    )
    await state.set_state(PassengerOrder.passengers_count)

async def process_passengers_count(message: Message, state: FSMContext):
    is_pochta = False
    count = 0
    
    if message.text == BTN_POCHTA:
        is_pochta = True
    elif message.text.isdigit() and 1 <= int(message.text) <= 6:
        count = int(message.text)
    else:
        await message.answer(
            "❌ Iltimos, to'g'ri qiymat kiriting:",
            reply_markup=get_passenger_count_keyboard()
        )
        return
    
    await state.update_data(passengers_count=count, is_pochta=is_pochta)
    
    await message.answer(
        PASSENGER_PHONE_NUMBER,
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(PassengerOrder.phone_number)

async def process_phone_number(message: Message, state: FSMContext):
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    await update_user_phone(message.from_user.id, phone)
    await state.update_data(phone_number=phone)
    
    await message.answer(
        PASSENGER_NOTE,
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PassengerOrder.note)

async def process_note(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(note=message.text)
    
    data = await state.get_data()
    
    order_id = await create_order(
        message.from_user.id,
        data["direction"],
        data["passengers_count"],
        data.get("is_pochta", False),
        data["note"]
    )
    
    await message.answer(
        PASSENGER_ORDER_COMPLETE,
        reply_markup=get_menu_keyboard()
    )
    
    order = await get_order(order_id)
    
    if DRIVERS_GROUP_ID:
        passengers_text = "📦 Pochta" if order["is_pochta"] else f"👥 {order['passengers_count']} kishi"
        
        await bot.send_message(
            DRIVERS_GROUP_ID,
            NEW_ORDER_GROUP.format(
                full_name=order["full_name"],
                direction=order["direction"],
                passengers_count=passengers_text,
                phone_number=order["phone_number"],
                note=order["note"] or "Yo'q"
            )
        )
    
    drivers = await get_all_drivers()
    for driver in drivers:
        if driver["is_active"] and not driver["is_banned"]:
            passengers_text = "📦 Pochta" if order["is_pochta"] else f"👥 {order['passengers_count']} kishi"
            
            await bot.send_message(
                driver["user_id"],
                NEW_ORDER_NOTIFICATION.format(
                    direction=order["direction"],
                    passengers_count=passengers_text,
                    note=order["note"] or "Yo'q"
                )
            )
    
    await state.clear()

async def process_inline_direction(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    direction = "Toshkent➡️Samarqand" if callback.data == "direction_tashkent_samarkand" else "Samarqand➡️Toshkent"
    await state.update_data(direction=direction)
    
    await callback.message.answer(
        PASSENGER_FULL_NAME,
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PassengerOrder.full_name)

def register_passenger_handlers(dp: Dispatcher):
    dp.message.register(process_direction, PassengerOrder.direction)
    dp.message.register(process_full_name, PassengerOrder.full_name)
    dp.message.register(process_passengers_count, PassengerOrder.passengers_count)
    dp.message.register(process_phone_number, PassengerOrder.phone_number, F.contact | F.text)
    dp.message.register(process_note, PassengerOrder.note)
    dp.callback_query.register(process_inline_direction, F.data.startswith("direction_"))""",
        
        "handlers/admin.py": """from aiogram import Dispatcher, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import ADMIN_ID, DRIVERS_GROUP_ID
from utils.states import AdminStates
from utils.text_messages import *
from keyboards.inline import (
    get_admin_keyboard,
    get_drivers_list_keyboard,
    get_driver_action_keyboard,
    get_back_to_admin_keyboard,
    get_orders_list_keyboard
)
from database.operations import (
    is_admin,
    get_statistics,
    get_all_drivers,
    ban_user,
    add_admin,
    get_all_users,
    get_active_orders
)

async def cmd_admin(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    
    await state.clear()
    
    await message.answer(
        ADMIN_WELCOME,
        reply_markup=get_admin_keyboard()
    )

async def process_admin_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        ADMIN_WELCOME,
        reply_markup=get_admin_keyboard()
    )

async def process_admin_stats(callback: CallbackQuery):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    stats = await get_statistics()
    
    await callback.message.edit_text(
        ADMIN_STATS.format(
            total_users=stats["total_users"],
            total_drivers=stats["total_drivers"],
            active_drivers=stats["active_drivers"],
            total_orders=stats["total_orders"],
            active_orders=stats["active_orders"]
        ),
        reply_markup=get_back_to_admin_keyboard()
    )

async def process_admin_drivers(callback: CallbackQuery):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    drivers = await get_all_drivers()
    
    if not drivers:
        await callback.message.edit_text(
            "🚫 Haydovchilar ro'yxati bo'sh.",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "🚕 *Haydovchilar ro'yxati:*",
        reply_markup=get_drivers_list_keyboard(drivers)
    )

async def process_admin_orders(callback: CallbackQuery):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    orders = await get_active_orders()
    
    if not orders:
        await callback.message.edit_text(
            "🚫 Faol buyurtmalar yo'q.",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📋 *Faol buyurtmalar:*",
        reply_markup=get_orders_list_keyboard(orders)
    )

async def process_driver_action(callback: CallbackQuery):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    driver_id = int(callback.data.split("_")[1])
    
    drivers = await get_all_drivers()
    
    driver = next((d for d in drivers if d["user_id"] == driver_id), None)
    
    if not driver:
        await callback.message.edit_text(
            "🚫 Haydovchi topilmadi.",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    status = "✅ Faol" if not driver["is_banned"] and driver["is_active"] else "❌ Faol emas"
    
    await callback.message.edit_text(
        f"👤 *Haydovchi ma'lumotlari:*\n\n"
        f"👤 Ism: {driver['full_name']}\n"
        f"🚗 Avtomobil: {driver['car_name']}\n"
        f"👥 O'rindiqlar: {driver['seats_count']}\n"
        f"📱 Telefon: {driver['phone_number']}\n"
        f"📊 Holat: {status}",
        reply_markup=get_driver_action_keyboard(driver_id, driver["is_banned"])
    )

async def process_ban_unban(callback: CallbackQuery):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    action, driver_id = callback.data.split("_")
    driver_id = int(driver_id)
    
    if action == "ban":
        await ban_user(driver_id, True)
        await callback.answer("🚫 Haydovchi bloklandi.")
    else:
        await ban_user(driver_id, False)
        await callback.answer("✅ Haydovchi blokdan chiqarildi.")
    
    await process_admin_drivers(callback)

async def process_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        ADMIN_BROADCAST_PROMPT,
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.waiting_for_broadcast_message)

async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin(message.from_user.id):
        return
    
    users = await get_all_users()
    
    sent_count = 0
    for user in users:
        try:
            await bot.send_message(user["user_id"], message.text)
            sent_count += 1
        except Exception:
            continue
    
    await message.answer(
        ADMIN_BROADCAST_SENT.format(count=sent_count),
        reply_markup=get_admin_keyboard()
    )
    
    await state.clear()

async def process_admin_add_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        ADMIN_ADD_ADMIN_PROMPT,
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.waiting_for_admin_id)

async def process_add_admin(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    
    if not message.text.isdigit():
        await message.answer(
            "❌ Noto'g'ri ID format. Iltimos, raqamli ID kiriting.",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return
    
    new_admin_id = int(message.text)
    await add_admin(new_admin_id, message.from_user.id)
    
    await message.answer(
        ADMIN_ADDED,
        reply_markup=get_admin_keyboard()
    )
    
    await state.clear()

async def process_admin_set_group(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        ADMIN_SET_GROUP_PROMPT,
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.waiting_for_group_id)

async def process_set_group(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    
    if not message.text.startswith("-") or not message.text[1:].isdigit():
        await message.answer(
            "❌ Noto'g'ri guruh ID format. Iltimos, to'g'ri ID kiriting (masalan: -1001234567890).",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return
    
    global DRIVERS_GROUP_ID
    DRIVERS_GROUP_ID = int(message.text)
    
    await message.answer(
        ADMIN_GROUP_SET,
        reply_markup=get_admin_keyboard()
    )
    
    await state.clear()

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(cmd_admin, Command("admin"))
    dp.callback_query.register(process_admin_menu, F.data == "admin_menu")
    dp.callback_query.register(process_admin_stats, F.data == "admin_stats")
    dp.callback_query.register(process_admin_drivers, F.data == "admin_drivers")
    dp.callback_query.register(process_admin_orders, F.data == "admin_orders")
    dp.callback_query.register(process_driver_action, F.data.startswith("driver_"))
    dp.callback_query.register(process_ban_unban, F.data.startswith("ban_") | F.data.startswith("unban_"))
    dp.callback_query.register(process_admin_broadcast, F.data == "admin_broadcast")
    dp.message.register(process_broadcast_message, AdminStates.waiting_for_broadcast_message)
    dp.callback_query.register(process_admin_add_admin, F.data == "admin_add_admin")
    dp.message.register(process_add_admin, AdminStates.waiting_for_admin_id)
    dp.callback_query.register(process_admin_set_group, F.data == "admin_set_group")
    dp.message.register(process_set_group, AdminStates.waiting_for_group_id)""",
        
        "handlers/common.py": """from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.text_messages import BTN_CANCEL
from keyboards.reply import get_role_keyboard
from utils.text_messages import WELCOME_MESSAGE

async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        return
    
    await state.clear()
    
    await message.answer(
        "❌ Bekor qilindi.",
        reply_markup=get_role_keyboard()
    )
    
    await message.answer(WELCOME_MESSAGE)

def register_common_handlers(dp: Dispatcher):
    dp.message.register(cancel_handler, F.text == BTN_CANCEL)"""
    }
    
    for file_path, content in files.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Created file: {file_path}")

def main():
    print("🚀 Starting Taxi Bot setup...")
    create_folder_structure()
    create_files()
    print("\n✨ Setup completed! Your Taxi Bot is ready to run.")
    print("\n📋 To run the bot, execute the following command:")
    print("   python main.py")

if __name__ == "__main__":
    main()