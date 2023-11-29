from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    location = Column(String)
    organization = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")
    nosql_collections = relationship("NoSqlCollection", back_populates="owner")
    projects = relationship("Project", back_populates="owner")
    workflows = relationship("Workflow", back_populates="owner")
    tasks = relationship("Task", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")


class NoSqlCollection(Base):
    __tablename__ = "nosql_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    collection_path = Column(String)

    owner = relationship("User", back_populates="nosql_collections")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    # organization = Column(String)
    # tasks = Column(String)
    owner = relationship("User", back_populates="projects")

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer)
    # organization = Column(String)
    # tasks = Column(String)
    owner = relationship("User", back_populates="workflows")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    # organization_id = Column(String)
    task_code = Column(String)
    project_id = Column(Integer)
    workflow_id = Column(Integer)
    workflow_order_id = Column(Integer)
    owner = relationship("User", back_populates="tasks")
