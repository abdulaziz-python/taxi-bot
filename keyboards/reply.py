from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.text_messages import *
from config import SUPPORT_USERNAME

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
    return keyboard

def get_help_keyboard():
    keyboard = [
        [
            KeyboardButton(text="📞 Bog'lanish", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")
        ],
        [
            KeyboardButton(text="📋 Menyu")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )