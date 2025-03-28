from aiogram import Dispatcher
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
        handler(dp)