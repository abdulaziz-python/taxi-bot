from aiogram import Dispatcher, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.states import UserRole
from utils.text_messages import WELCOME_MESSAGE
from keyboards.reply import get_role_keyboard, get_driver_menu_keyboard, get_help_keyboard
from database.operations import add_user, update_user_role, get_user, is_driver
from handlers.driver import start_driver_registration
from handlers.passenger import start_passenger_order

async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    await add_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username
    )
    
    user = await get_user(message.from_user.id)
    
    if user and user["role"]:
        if user["role"] == "driver":
            if await is_driver(message.from_user.id):
                from utils.text_messages import DRIVER_MENU
                await message.answer(
                    DRIVER_MENU,
                    reply_markup=get_driver_menu_keyboard()
                )
            else:
                await start_driver_registration(message, state)
        elif user["role"] == "passenger":
            await start_passenger_order(message, state)
    else:
        # New user or user without role, show role selection
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=get_role_keyboard()
        )
        
        await state.set_state(UserRole.choosing_role)

async def process_role_selection(message: Message, state: FSMContext, bot: Bot):
    from utils.text_messages import BTN_DRIVER, BTN_PASSENGER
    from database.operations import notify_admin_new_user
    
    if message.text == BTN_DRIVER:
        await update_user_role(message.from_user.id, "driver")
        await notify_admin_new_user(
            bot, 
            message.from_user.id, 
            message.from_user.full_name, 
            message.from_user.username, 
            "driver"
        )
        await start_driver_registration(message, state)
    
    elif message.text == BTN_PASSENGER:
        await update_user_role(message.from_user.id, "passenger")
        await notify_admin_new_user(
            bot, 
            message.from_user.id, 
            message.from_user.full_name, 
            message.from_user.username, 
            "passenger"
        )
        await start_passenger_order(message, state)
    
    else:
        await message.answer(
            "Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=get_role_keyboard()
        )

async def cmd_menu(message: Message, state: FSMContext):
    await cmd_start(message, state)

async def cmd_help(message: Message):
    from config import SUPPORT_USERNAME
    help_text = (
        "🤖 *Taxi Bot Yordami*\n\n"
        "📋 *Asosiy buyruqlar:*\n"
        "/start \\- Botni ishga tushirish\n"
        "/menu \\- Asosiy menyuga qaytish\n"
        "/help \\- Yordam xabarini ko'rsatish\n"
        "/admin \\- Admin paneliga kirish \\(faqat adminlar uchun\\)\n\n"
        "🚕 *Haydovchilar uchun:*\n"
        "1\\. Ro'yxatdan o'tish uchun /start buyrug'ini bosing\n"
        "2\\. Avtomobil ma'lumotlarini kiriting\n"
        "3\\. Faol/No faol holatni tanlang\n\n"
        "👤 *Yo'lovchilar uchun:*\n"
        "1\\. /start buyrug'ini bosing\n"
        "2\\. Yo'nalishni tanlang\n"
        "3\\. Ma'lumotlarni kiriting\n"
        "4\\. Haydovchi siz bilan bog'lanadi\n\n"
        "❓ *Savollar bo'lsa:*\n"
        f"Admin bilan bog'laning: {SUPPORT_USERNAME}"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_help_keyboard(),
        parse_mode="MarkdownV2"
    )

def register_start_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_menu, Command("menu"))
    dp.message.register(cmd_menu, F.text == "📋 Menyu")
    dp.message.register(process_role_selection, UserRole.choosing_role)
    dp.message.register(cmd_help, Command("help"))