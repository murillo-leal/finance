from cs50 import SQL

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Create table for user balance
db.execute("""
CREATE TABLE IF NOT EXISTS 'balances' (
    'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'user_id' INTEGER NOT NULL,
    'symbol' TEXT NOT NULL,
    'shares' INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_balances_user_id_symbol ON balances (user_id, symbol)")    

# Create table of user history
db.execute("""
CREATE TABLE IF NOT EXISTS 'history' (
    'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'user_id' INTEGER, 'symbol' TEXT,
    'shares' INTEGER NOT NULL,
    'price' NUMERIC NOT NULL,
    'created_at' DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)    
    )
    """)
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS index_history_user_id ON balances (user_id, symbol)")  