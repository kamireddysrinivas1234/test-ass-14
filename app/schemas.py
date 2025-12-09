from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CalculationType(str, Enum):
    add = "add"
    sub = "sub"
    mul = "mul"
    div = "div"

class CalculationCreate(BaseModel):
    type: CalculationType
    a: float
    b: float

    @field_validator("b")
    @classmethod
    def no_zero_divisor(cls, v, info):
        # Pydantic v2: info.data contains validated fields so far
        calc_type = info.data.get("type")
        if calc_type == CalculationType.div and v == 0:
            raise ValueError("b cannot be zero for division")
        return v

class CalculationUpdate(BaseModel):
    type: Optional[CalculationType] = None
    a: Optional[float] = None
    b: Optional[float] = None

class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: CalculationType
    result: float
    user_id: int
    class Config:
        from_attributes = True
