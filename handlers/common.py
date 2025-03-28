from aiogram import Dispatcher, F
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
        "❌ Bekor qilindi\\.",
        reply_markup=get_role_keyboard(),
        parse_mode="MarkdownV2"
    )
    
    await message.answer(
        WELCOME_MESSAGE,
        parse_mode="MarkdownV2"
    )

def register_common_handlers(dp: Dispatcher):
    dp.message.register(cancel_handler, F.text == BTN_CANCEL)