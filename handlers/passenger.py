from aiogram import Dispatcher, F, Bot
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
                full_name=data["full_name"],
                direction=order["direction"].replace("+", "\\+").replace(".", "\\.").replace("-", "\\-"),
                passengers_count=passengers_text,
                phone_number=order["phone_number"].replace("+", "\\+").replace("-", "\\-"),
                note=order["note"] or "Yo'q"
            ),
            parse_mode="MarkdownV2"
        )
    
    drivers = await get_all_drivers()
    for driver in drivers:
        if driver["is_active"] and not driver["is_banned"]:
            passengers_text = "📦 Pochta" if order["is_pochta"] else f"👥 {order['passengers_count']} kishi"
            
            await bot.send_message(
                driver["user_id"],
                NEW_ORDER_NOTIFICATION.format(
                    direction=order["direction"].replace("+", "\\+").replace(".", "\\.").replace("-", "\\-"),
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
    dp.callback_query.register(process_inline_direction, F.data.startswith("direction_"))