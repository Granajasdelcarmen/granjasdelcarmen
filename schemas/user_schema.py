from pydantic import BaseModel

class UserBase(BaseModel):
    first_name: str
    last_name: str
    phone: str | None = None
    email: str
    password: str
