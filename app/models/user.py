from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class User(BaseModel):
    id: str
    email: EmailStr
    full_name: str
