from aiogram import Dispatcher, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from aiogram.exceptions import TelegramBadRequest
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
    get_active_orders,
    set_drivers_group
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
    
    try:
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
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

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
    
    # Maxsus belgilarni qochirish
    safe_full_name = driver['full_name'].replace('.', '\\.').replace('-', '\\-').replace('+', '\\+')
    safe_car_name = driver['car_name'].replace('.', '\\.').replace('-', '\\-').replace('+', '\\+')
    
    await callback.message.edit_text(
        f"👤 *Haydovchi ma'lumotlari:*\n\n"
        f"👤 Ism: {safe_full_name}\n"
        f"🚗 Avtomobil: {safe_car_name}\n"
        f"👥 O'rindiqlar: {driver['seats_count']}\n"
        f"📱 Telefon: {driver['phone_number'].replace('+', '\\+').replace('-', '\\-')}\n"
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
            await bot.forward_message(
                chat_id=user["user_id"],
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
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
            "❌ Noto'g'ri ID format\\. Iltimos, raqamli ID kiriting\\.",
            reply_markup=get_admin_keyboard(),
            parse_mode="MarkdownV2"
        )
        await state.clear()
        return
    
    new_admin_id = int(message.text)
    await add_admin(new_admin_id, message.from_user.id)
    
    await message.answer(
        ADMIN_ADDED,
        reply_markup=get_admin_keyboard(),
        parse_mode="MarkdownV2"
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
            "❌ Noto'g'ri guruh ID format\\. Iltimos, to'g'ri ID kiriting\\. Misol: \\-1001234567890",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return
    
    await set_drivers_group(int(message.text))
    
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
    dp.message.register(process_set_group, AdminStates.waiting_for_group_id)