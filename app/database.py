import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')
# Open database connection
conn = sqlite3.connect(DATABASE_PATH)

# Create users table
conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userId INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        email TEXT,
        firstName TEXT,
        lastName TEXT,
        address1 TEXT,
        address2 TEXT,
        zipcode TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        phone TEXT
    )
''')

# Create books table
conn.execute('''
    CREATE TABLE IF NOT EXISTS books (
        bookId INTEGER PRIMARY KEY,
        title TEXT,
        author TEXT,
        price REAL,
        stock INTEGER,
        image TEXT,
        categoryId INTEGER,
        FOREIGN KEY(categoryId) REFERENCES categories(categoryId)
    )
''')

# Create categories table
conn.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        categoryId INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
''')

# Create orders table
conn.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        orderId INTEGER PRIMARY KEY,
        userId INTEGER,
        total REAL,
        date TEXT,
        FOREIGN KEY(userId) REFERENCES users(userId)
    )
''')

# Create order_items table
conn.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        orderItemId INTEGER PRIMARY KEY,
        orderId INTEGER,
        bookId INTEGER,
        quantity INTEGER,
        FOREIGN KEY(orderId) REFERENCES orders(orderId),
        FOREIGN KEY(bookId) REFERENCES books(bookId)
    )
''')

# Create kart table (NEW)
conn.execute('''
    CREATE TABLE IF NOT EXISTS kart (
        cartId INTEGER PRIMARY KEY AUTOINCREMENT,
        userId INTEGER,
        bookId INTEGER,
        quantity INTEGER,
        FOREIGN KEY(userId) REFERENCES users(userId),
        FOREIGN KEY(bookId) REFERENCES books(bookId)
    )
''')

# Commit and close the connection
conn.commit()
conn.close()

print("Database initialized with the users, books, categories, orders, order_items, and kart tables.")
