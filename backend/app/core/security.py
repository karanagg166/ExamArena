import bcrypt
def get_password_hash(password:str):
    salt=bcrypt.gensalt(10)
    return bcrypt.hashpw(password.encode('utf-8'),salt).decode('utf-8')