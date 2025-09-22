import email
from email import message
from pydantic import BaseModel,Field, model_validator
from typing_extensions import Annotated


    

class add_stuedent:
    name:str
    id:int
    email:str
    departement:str

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class LoginUser(BaseModel):     
    email: str
    password: str
class ResetPasswordRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    new_password: str = Field(..., example="MySecret123")
    confirm_password: str = Field(..., example="MySecret123")

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
    
    

