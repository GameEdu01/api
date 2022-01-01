from pydantic import BaseModel


class Login(BaseModel):  # Login basic model
    username: str
    password: str


class SignUp(Login):  # SignUp basic model
    email: str


class AdminUserRequest(Login):  # Admin any user request basic model
    user_username: str


class LoginWithSession(BaseModel):  # When you want to use your session
    username: str
    session: str


class ChangeNick(Login):  # Login, but also with nickname
    nickname: str


class WalletSignUp(BaseModel):  # Connect a wallet to user
    name: str
    surname: str
    email: str
    phone_number: str
    password: str