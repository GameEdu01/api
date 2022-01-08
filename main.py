from fastapi import FastAPI
import time
import os

from scr.dbconnector import DBConnector
from scr.config import Config
from scr.manager import Manager
from scr.request_form import *


manager = Manager()
config = Config("config.json")
app = FastAPI()
db = DBConnector(dbname="d2d1ljqhqhl34q",
                 user="udmehkiskcczbm",
                 password=os.environ.get("DB_USER_PASSWORD"),
                 address=("ec2-54-161-164-220.compute-1.amazonaws.com", "5432"),
                 config=config)


@app.post("/api/hello", response_description="Just to make sure api is working")  # Hello world!
async def get_root():

    return {"message": "Hello my guy!"}


@app.post("/api/change_nick", response_description=config.configData["descriptions"]["change_nick"])
async def change_nick(login: ChangeNick):  # Change user's nickname

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.password):
        return {"message": "check your spelling at password field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}
    if not manager.check_spelling(login.nickname):
        return {"message": "Use an appropriate nickname"}

    db.change_nickname(login.username, login.nickname)

    return {"message": "{} nickname was changed to {}".format(login.username, login.nickname)}


@app.post("/api/update_session_expire_date", response_description=config.configData["descriptions"]["update_session_expire_date"])
async def update_session_expire_date(login: Login):

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.password):
        return {"message": "check your spelling at password field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired, make a new session!"}

    db.update_session_expire(login.username)

    return {"message": "session expire was updated"}


@app.post("/api/new_session", response_description=config.configData["descriptions"]["new_session"])
async def new_session(login: LoginWithSession):

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.session, email=True):
        return {"message": "check your spelling at session field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user["session"] == login.session:
        return {"message": "This is not your current session!"}
    if user["is_active"] and user["session_expire"] > time.time():
        return {"message": "You already have a working session! You can't make a new one until it expires"}

    session, time_created = manager.get_secret(30, "")
    time_created += config.configData["session_length"]

    db.change_session(login.username, session, time_created)
    db.set_is_active(login.username, True)

    return {"message": "new session created for user {}".format(login.username),
            "session": session}


@app.post("/api/get_session", response_description=config.configData["descriptions"]["get_session"])
async def get_session(login: Login):

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.password):
        return {"message": "check your spelling at password field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}

    return {"message": "session found",
            "session": user["session"]}


@app.post("/api/set_user_active_with_session", response_description=config.configData["descriptions"]["set_user_active_with_session"])
async def set_user_active_with_session(login: LoginWithSession):

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.session, email=True):
        return {"message": "check your spelling at session field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user["session"] == login.session:
        return {"message": "This session is not the same as in database / wrong session key"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired! Please make a new session"}

    db.set_is_active(login.username, True)

    return {"message": "Set active successfully!"}


@app.post("/api/get_table", response_description=config.configData["descriptions"]["get_table"])  # get table from the database by it's name
async def get_table(table_name: str, login: Login):

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.password):
        return {"message": "check your spelling at password field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}
    if not user["is_superuser"]:
        return {"message": "This user is not a superuser, so he can't access it"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    return {"message": "table sent",
            "table": db.get_table(table_name)}


@app.post("/api/get_user_with_admin", response_description=config.configData["descriptions"]["get_user_with_admin"])
async def get_user_with_admin(aur: AdminUserRequest):

    if not manager.check_spelling(aur.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(aur.password):
        return {"message": "check your spelling at password field"}
    if not manager.check_spelling(aur.user_username):
        return {"message": "check your spelling at username you are looking for field"}

    if not db.value_exists("users", aur.username, "username"):
        return {"message": "This admin user does not exist"}

    user = db.get_user_data(aur.username)

    if not user:
        return {"message": "Incorrect admin username or password"}
    if not user["password"] == hash(aur.password):
        return {"message": "Incorrect admin username or password"}
    if not user["is_superuser"]:
        return {"message": "You don't have access to this make this request!"}
    if user["session_expire"] <= time.time():
        db.set_is_active(aur.username, False)
        return {"message": "This session is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This admin user is not active"}

    if not db.value_exists("users", aur.user_username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(aur.user_username)

    return {aur.user_username: user}


# NOTE I've completely removed go api from this script


@app.post("/api/get_user", response_description=config.configData["descriptions"]["get_user"])
async def get_user(login: Login):  # get user, you must know the password in order to access it

    if not manager.check_spelling(signup.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(signup.password):
        return {"message": "check your spelling at password field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    return {login.username: user}


@app.post("/api/get_user_demo/{username}", response_description=config.configData["descriptions"]["get_user_demo"])
async def get_user_demo(username: str):

    if not manager.check_spelling(username):
        return {"message": "check your spelling at username field"}

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

    if not manager.check_spelling(signup.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(signup.password):
        return {"message": "check your spelling at password field"}
    if not manager.check_spelling(signup.email, email=True):
        return {"message": "check your spelling at email field"}

    userExists = db.value_exists("users", signup.username, "username")
    emailExists = db.value_exists("users", signup.email, "email")
    if userExists or emailExists:
        return {"message": "This username or email already exists!"}

    signup.password = hash(signup.password)

    token, _ = manager.get_secret(60, "TTT")
    session, time_created = manager.get_secret(30, "")

    db.signup_user(signup, token, session, time_created)

    return {"message": f"{signup.username} was added to database",
            "token": token}


@app.post("/api/wallet_signup", response_description=config.configData["descriptions"]["wallet_signup"])
async def wallet_signup(login: WalletSignUp):

    if not manager.check_spelling(login.name):
        return {"message": "check your spelling at name field"}
    if not manager.check_spelling(login.surname):
        return {"message": "check your spelling at surname field"}
    if not manager.check_spelling(login.email, email=True):
        return {"message": "check your spelling at email field"}
    if not manager.check_spelling(login.phone_number, phone_number=True):
        return {"message": "check your spelling at phone_number field"}

    if not db.value_exists("users", login.email, "email"):
        return {"message": "User with that email does not exist"}

    if db.value_exists("m_users", login.email, "email"):
        return {"message": "this email already exists"}
    if db.value_exists("m_users", login.phone_number, "phone_number"):
        return {"message": "this phone number already exists"}

    user = db.get_user_data(None, login.email)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(user["username"], False)
        return {"message": "This session is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    db.signup_user_wallet(login)

    return {"message": "user signed up successfully",
            "first_name": login.name,
            "last_name": login.surname}


@app.post("/api/get_wallet", response_description=config.configData["descriptions"]["get_user_wallet"])
async def get_user_wallet(login: SignUp):

    if not manager.check_spelling(login.username):
        return {"message": "check your spelling at username field"}
    if not manager.check_spelling(login.password):
        return {"message": "check your spelling at password field"}
    if not manager.check_spelling(login.email, email=True):
        return {"message": "check your spelling at email field"}

    if not db.value_exists("users", login.username, "username"):
        return {"message": "This user does not exist"}

    user = db.get_user_data(login.username)

    if not user:
        return {"message": "Incorrect username or password"}
    if not user["password"] == hash(login.password):
        return {"message": "Incorrect username or password"}
    if user["session_expire"] <= time.time():
        db.set_is_active(login.username, False)
        return {"message": "This session is expired, make a new session!"}
    if not user["is_active"]:
        return {"message": "This user is not active"}

    walletExists = db.value_exists("m_users", login.email, "email")

    if not walletExists:
        return {"message": "{} does not have a wallet connected".format(login.email)}

    wallet = db.get_value_from_string("m_users", login.email, "email")

    return {"message": "wallet was found",
            "wallet": wallet}


# before running, use
# pip install -r requirements.txt

# YOU MUST PULL WHOLE fastApi BRANCH IN ORDER FOR THIS TO WORK
# Because i use other files with this script

# If you want to run this script locally on your machine:
# uvicorn api:app --reload

# Then go into http://127.0.0.1:8000/docs and you'll see the documentation
