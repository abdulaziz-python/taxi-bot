from aiogram import Dispatcher, F, Bot
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

async def process_car_photo(message: Message, state: FSMContext, bot: Bot):
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
    
    from database.operations import notify_admin_new_driver
    await notify_admin_new_driver(
        bot,
        message.from_user.id,
        data["full_name"],
        data["car_name"],
        data["seats_count"]
    )
    
    await message.answer(
        DRIVER_REGISTRATION_COMPLETE,
        reply_markup=get_driver_menu_keyboard()
    )
    
    await state.clear()

async def process_driver_status(message: Message, state: FSMContext):
    if message.text == BTN_DRIVER_ACTIVE:
        await toggle_driver_status(message.from_user.id, True)
        await message.answer("✅ Siz faol holatdasiz\\. Yangi buyurtmalar haqida xabardor qilinasiz\\.", reply_markup=get_driver_menu_keyboard())
    
    elif message.text == BTN_DRIVER_INACTIVE:
        await toggle_driver_status(message.from_user.id, False)
        await message.answer("❌ Siz faol emas holatidasiz\\. Yangi buyurtmalar haqida xabardor qilinmaysiz\\.", reply_markup=get_driver_menu_keyboard())

async def cmd_menu(message: Message, state: FSMContext):
    await cmd_start(message, state)

def register_driver_handlers(dp: Dispatcher):
    dp.message.register(process_car_name, DriverRegistration.car_name)
    dp.message.register(process_seats_count, DriverRegistration.seats_count)
    dp.message.register(process_full_name, DriverRegistration.full_name)
    dp.message.register(process_phone_number, DriverRegistration.phone_number, F.contact | F.text)
    dp.message.register(process_car_photo, DriverRegistration.car_photo, F.photo)
    dp.message.register(process_driver_status, F.text.in_([BTN_DRIVER_ACTIVE, BTN_DRIVER_INACTIVE]))