import asyncpg
from config import DATABASE_URL, ADMIN_ID

async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            phone_number TEXT,
            role TEXT,
            is_banned BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await conn.execute('''
        INSERT INTO users (user_id, full_name, username, role)
        VALUES ($1, 'Admin', 'admin', 'admin')
        ON CONFLICT (user_id) DO NOTHING
    ''', ADMIN_ID)
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
            car_name TEXT,
            seats_count INTEGER,
            car_photo TEXT,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            passenger_id BIGINT REFERENCES users(user_id),
            direction TEXT,
            passengers_count INTEGER,
            is_pochta BOOLEAN DEFAULT FALSE,
            note TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
            added_by BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await conn.execute('''
        INSERT INTO admins (user_id, added_by)
        VALUES ($1, $1)
        ON CONFLICT (user_id) DO NOTHING
    ''', ADMIN_ID)
    
    await conn.close()