from fastapi import FastAPI
from pydantic import BaseModel
from cryptography.fernet import Fernet
import random
import string
import time
from scr.dbconnector import DBConnector
from scr.config import Config
import os


key = os.environ.get("SECRET_KEY").encode()  # Key used to encrypt secrets, will be hidden in the .env in future
fernet = Fernet(key)


def get_secret(length, start):

    secret = start
    for i in range(length):
        if not i == 0 and not i == length - 1:
            if random.randint(1, 6) == 1:
                secret += "."
                continue
        secret += random.choice(string.ascii_letters)

    dt = time.time()

    return secret, dt


# NOTE i am planning to make a single function instead of user_exists() and email_exists()
# PS DONE


config = Config("config.json")
app = FastAPI()
db = DBConnector(dbname="d2d1ljqhqhl34q",
                 user="udmehkiskcczbm",
                 password=os.environ.get("DB_USER_PASSWORD"),
                 address=("ec2-54-161-164-220.compute-1.amazonaws.com", "5432"),
                 config=config)


class Login(BaseModel):  # Login basic model
    username: str
    password: str


class SignUp(Login):  # SignUp basic model
    email: str


class AdminUserRequest(Login):  # Admin basic model
    user_username: str


class LoginWithSession(BaseModel):  # When you want to use your session
    username: str
    session: str


class ChangeNick(Login):  # Login, but also with nickname
    nickname: str


@app.post("/api/hello")  # Hello world!
async def get_root():
    return {"Hello": "World!"}


@app.post("/api/change_nick", response_description=config.configData["descriptions"]["change_nick"])
async def change_nick(login: ChangeNick):  # Change user's nickname

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not fernet.decrypt(user["password"].encode()).decode() == login.password:
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This sesssion is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}
    if not db.check_spelling(login.nickname):
        return {"message": "Use an appropriate nickname"}

    db.change_nickname(login.username, login.nickname)

    return {"message": "{} nickname was changed to {}".format(login.username, login.nickname)}


@app.post("/api/update_session_expire_date", response_description=config.configData["descriptions"]["update_session_expire_date"])
async def update_session_expire_date(login: Login):
    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not fernet.decrypt(user["password"].encode()).decode() == login.password:
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This sesssion is expired, make a new session!"}

    db.update_session_expire(login.username)

    return {"message": "session expire was updated"}


@app.post("/api/new_session", response_description=config.configData["descriptions"]["new_session"])
async def new_session(login: LoginWithSession):
    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user["session"] == login.session:
        return {"message": "This is not your current session!"}
    if user["is_active"] and user["session_expire"] > time.time():
        return {"message": "You already have a working session! You can't make a new one untill it expires"}

    session, time_created = get_secret(30, "")
    time_created += config.configData["session_lenght"]

    db.change_session(login.username, session, time_created)
    db.set_is_active(login.username, True)

    return {"session": session}


@app.post("/api/get_session", response_description=config.configData["descriptions"]["get_session"])
async def get_session(login: Login):
    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not fernet.decrypt(user["password"].encode()).decode() == login.password:
        return {"message": "Incorrect username or password"}

    return {"session": user["session"]}


@app.post("/api/set_user_active_with_session", response_description=config.configData["descriptions"]["set_user_active_with_session"])
async def set_user_active_with_session(login: LoginWithSession):
    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user["session"] == login.session:
        return {"message": "This session is not the same as in database / wrong session key"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired! Please make a new session"}

    db.set_is_active(login.username, True)

    return {"message": "Set active sucessfully!"}


@app.post("/api/get_table", response_description=config.configData["descriptions"]["get_table"])  # get table from the database by it's name
async def get_table(table_name: str, login: Login):
    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not fernet.decrypt(user["password"].encode()).decode() == login.password:
        return {"message": "Incorrect username or password"}
    if not user["is_superuser"]:
        return {"message": "This user is not a superuser, so he can't access it"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This sesssion is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    return db.get_table(table_name)


@app.post("/api/get_user_with_admin", response_description=config.configData["descriptions"]["get_user_with_admin"])
async def get_user_with_admin(aur: AdminUserRequest):
    if not db.value_exists("users", aur.username, "username"):
        return {"message": "This admin user does not exist"}

    user = db.get_user_data(aur.username)

    if not user:
        return {"message": "Incorrect admin username or password"}
    if not fernet.decrypt(user["password"].encode()).decode() == aur.password:
        return {"message": "Incorrect admin username or password"}
    if not user["is_superuser"]:
        return {"message": "You don't have access to this request!"}
    if user["session_expire"] <= time.time():
        db.set_is_active(aur.username, False)
        return {"message": "This sesssion is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    if not db.value_exists("users", aur.user_username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(aur.user_username)

    return {aur.user_username: user}


# NOTE I've completely removed go api from this script

# I created new "users" table for the signup function, i hope you like it so we can keep it for now


@app.post("/api/get_user", response_description=config.configData["descriptions"]["get_user"])
async def get_user(login: Login):  # get user, you must know the password in order to access it

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)

    if not user:
        return {"message": "Incorrect username or password"}
    if not fernet.decrypt(user["password"].encode()).decode() == login.password:
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This sesssion is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    return {login.username: user}


@app.post("/api/get_user_demo/{username}", response_description=config.configData["descriptions"]["get_user_demo"])
async def get_user_demo(username: str):
    if not db.value_exists("users", username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(username)

    del user["password"]
    del user["token"]
    del user["session"]
    del user["session_expire"]

    return {username: user}


@app.post("/api/signup", response_description=config.configData["descriptions"]["signup"])  # basic syntax check
async def signup(signup: SignUp):
    if " " in signup.email or not "@" in signup.email:
        return {"message": "Please use an appropriate email address"}
    if signup.email == "" or signup.password == "" or signup.username == "":
        return {"message": "No empty fields!"}
    if " " in signup.username:
        return {"message": "Username can not contain spaces"}
    if " " in signup.password:
        return {"message": "Password can not contain spaces"}
    if "'" in signup.password or "'" in signup.username or "'" in signup.email:
        return {"message": "No special characters"}
    if not signup.password.isascii() or not signup.email.isascii() or not signup.username.isascii():
        return {"message": "No special characters"}

    userExists = db.value_exists("users", signup.username, "username")
    emailExists = db.value_exists("users", signup.email, "email")
    if userExists or emailExists:
        return {"message": "This username or email already exists!"}

    signup.password = fernet.encrypt(signup.password.encode()).decode()

    token, _ = get_secret(60, "TTT")
    session, time_created = get_secret(30, "")

    db.cursor.execute("""INSERT INTO users (username, password, email, token, is_superuser, session, session_expire, is_active, money, time_spent_on_website)
        VALUES ('{}', '{}', '{}', '{}', false, '{}', {}, true, 0, 0)""".format(signup.username, signup.password,
                                                                               signup.email, token, session,
                                                                               time_created + config.configData[
                                                                                                          "session_lenght"]))

    db.conn.commit()  # Session expire is a time.time() object, i think it's easier to work with it

    return {"message": f"{signup.username} was added to database",
            "token": token}


# before running, use
# pip install -r requirements.txt

# YOU MUST PULL WHOLE fastApi BRANCH IN ORDER FOR THIS TO WORK
# Because i use other files with this script

# If you want to run this script localy on your machine:
# uvicorn api:app --reload

# Then go into http://127.0.0.1:8000/docs and you'll see the documentation
