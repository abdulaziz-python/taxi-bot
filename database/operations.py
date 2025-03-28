import asyncpg
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

async def is_driver(user_id):
    conn = await get_connection()
    driver = await conn.fetchrow('SELECT * FROM drivers WHERE user_id = $1', user_id)
    await conn.close()
    return driver is not None


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
    }

async def notify_admin_new_user(bot, user_id, full_name, username, role):
    from config import ADMIN_ID
    
    try:
        # Maxsus belgilarni qochirish
        safe_full_name = full_name.replace('.', '\\.').replace('-', '\\-').replace('+', '\\+')
        user_name_display = username or 'Yo\'q'
        
        await bot.send_message(
            ADMIN_ID,
            f"🆕 *Yangi foydalanuvchi qo'shildi*\n\n"
            f"👤 ID: `{user_id}`\n"
            f"📝 Ism: {safe_full_name}\n"
            f"🔖 Username: @{user_name_display}\n"
            f"🔍 Rol: {role}"
        )
    except Exception as e:
        print(f"Error notifying admin about new user: {e}")

async def notify_admin_new_driver(bot, user_id, full_name, car_name, seats_count):
    from config import ADMIN_ID
    
    try:
        # Maxsus belgilarni qochirish
        safe_full_name = full_name.replace('.', '\\.').replace('-', '\\-').replace('+', '\\+')
        safe_car_name = car_name.replace('.', '\\.').replace('-', '\\-').replace('+', '\\+')
        
        await bot.send_message(
            ADMIN_ID,
            f"🚕 *Yangi haydovchi qo'shildi*\n\n"
            f"👤 ID: `{user_id}`\n"
            f"📝 Ism: {safe_full_name}\n"
            f"🚗 Avtomobil: {safe_car_name}\n"
            f"👥 O'rindiqlar: {seats_count}"
        )
    except Exception as e:
        print(f"Error notifying admin about new driver: {e}")

async def set_drivers_group(group_id):
    import os
    from config import DRIVERS_GROUP_ID
    
    # Config faylni o'qish
    with open("config.py", "r") as file:
        content = file.read()
    
    # DRIVERS_GROUP_ID qatorini yangilash
    import re
    updated_content = re.sub(
        r'DRIVERS_GROUP_ID\s*=\s*.*',
        f'DRIVERS_GROUP_ID = {group_id}',
        content
    )
    
    # Yangilangan contentni yozish
    with open("config.py", "w") as file:
        file.write(updated_content)
    
    # Global DRIVERS_GROUP_ID ni yangilash
    import sys
    sys.modules["config"].DRIVERS_GROUP_ID = group_id