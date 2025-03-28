from aiogram.fsm.state import State, StatesGroup

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
    waiting_for_group_id = State()