from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_pass = get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, 
                          location=user.location, organization=user.organization, 
                          full_name=user.full_name, hashed_password=hashed_pass)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        return None

    db.delete(db_user)
    db.commit()
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None

    user_data = user_update.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_user_password(db: Session, user_id: int, new_password: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None

    hashed_password = get_password_hash(new_password)
    db_user.hashed_password = hashed_password

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_nosql_collection(db: Session, collection: schemas.NoSQLCollection, user: schemas.User):
    db_collection = models.NoSqlCollection(**collection.dict(), owner_id=user.id)
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    return db_collection


def get_nosql_collections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.NoSqlCollection).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectBase, user: schemas.User):
    db_project = models.Project(**project.dict(), owner_id=user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project_by_name(db: Session, name: str):
    return db.query(models.Project).filter(models.Project.name == name).first()


def get_project_by_id(db: Session, id: int):
    return db.query(models.Project).filter(models.Project.id == id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


def create_workflow(db: Session, workflow: schemas.ProjectBase, user: schemas.User, project: schemas.Project):
    # workflow = get_workflow_by_name(db=db, workflow=workflow.name)
    workflow_obj = get_project_workflow_by_name(db=db, workflow=workflow.name, project_id=project.id)
    if not workflow_obj:
        db_workflow = models.Workflow(**workflow.dict(), owner_id=user.id)
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        return db_workflow

def get_workflow_by_name(db: Session, workflow: str):
    return db.query(models.Workflow).filter(models.Workflow.name == workflow).first()


def get_project_workflow_by_name(db: Session, workflow: str, project_id: int):
    return db.query(models.Workflow).filter(models.Workflow.project_id == project_id).filter(models.Workflow.name == workflow).first()


def get_workflows(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Workflow).offset(skip).limit(limit).all()