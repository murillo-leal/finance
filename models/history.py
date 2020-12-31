from models.database import db

def get_history_by_user_id(user_id):
 rows = db.execute("SELECT * FROM history WHERE user_id = ?", user_id)         
 return rows


def insert_new_entry(user_id, symbol, shares, price):
    db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)", user_id, symbol, shares, price)


