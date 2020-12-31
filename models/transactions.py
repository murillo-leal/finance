from models.database import db

def sell(user_id, symbol, shares):   

        sucess, message = sell_user_shares(user_id, symbol, shares)
        stock = lookup(symbol)
        if not stock:
            return apology(f"error retrieving stock '{symbol}'", 400)

        users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        user = users[0]      

        

       