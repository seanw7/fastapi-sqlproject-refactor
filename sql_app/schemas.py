from pydantic import BaseModel, Field
from typing import Optional


class ItemBase(BaseModel):
    title: str
    description: str | None = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True
        # from_attributes = True

class NoSQLCollectionBase(BaseModel):
    name: str
    description: str | None = None
    collection_path: str | None = None

class NoSQLCollection(NoSQLCollectionBase):
    id: int
    owner_id: int
    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    name: str
    description: str | None = None

class Project(ProjectBase):
    id: int
    owner_id: int
    class Config:
        orm_mode = True

class WorkflowBase(BaseModel):
    name: str
    description: str | None = None
    project_id: int

class Workflow(WorkflowBase):
    id: int
    owner_id: int
    project_id: int
    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    name: str
    description: str | None = None
    task_code: str | None = None

class Task(TaskBase):
    id: int
    owner_id: int
    project_id: int | None = None
    workflow_id: int | None = None
    workflow_order_id: int | None = None

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: str
    username: str
    location: str | None = None
    organization: str | None = None
    full_name: str | None = None

class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: list[Item] = []
    nosql_collections: list[NoSQLCollection] = []
    projects: list[Project] = []

    class Config:
        orm_mode = True
        # from_attributes = True

class UserInDB(UserBase):
    hashed_password: str

class UserDelete(UserBase):
    id: str

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    location: Optional[str] = None
    organization: Optional[str] = None
    # Add other fields as necessary

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None