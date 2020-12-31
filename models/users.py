from models.database import db
from helpers import apology, login_required, lookup, usd
from werkzeug.security import check_password_hash, generate_password_hash



def get_user_by_id(user_id):
        users = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        if len(users):
            return users[0]
        else:
            return None

def get_user_by_username_and_password(username, password):
     # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            None
        else:                
            return rows[0]

def register(username, password):
       hashed_password = generate_password_hash(password)

       new_user_id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

       return new_user_id

def update_password(user_id,current_password, password):
    user = get_user_by_id(user_id)

    if not check_password_hash(user["hash"], current_password):
        return False  

    hashed_password = generate_password_hash(password)
    db.execute("UPDATE users SET hash = ? WHERE id = ?", hashed_password, user_id)
    return True       

def add_cash(user_id, amount):
    user = get_user_by_id(user_id)
    updated_cash = user["cash"] + amount
    db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user_id)
