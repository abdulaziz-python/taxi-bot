from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    return keyboard