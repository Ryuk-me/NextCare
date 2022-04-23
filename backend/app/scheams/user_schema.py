from datetime import datetime, date
from pydantic import BaseModel, EmailStr, constr
from typing import List, Literal
from app.scheams import appointment_schema


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: constr(max_length=10, min_length=10)
    gender: Literal['male', 'female', 'other']
    dob: date
    password: str


class ChangePassword(BaseModel):
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    profile_image: str
    gender: str
    phone:  str
    dob: date
    age: int
    created_at: datetime
    updated_at: datetime
    appointments: List[appointment_schema.AppointmentOut]

    class Config:
        orm_mode = True
