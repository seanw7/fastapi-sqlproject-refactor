import json
import os
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

# to get a string like this run:
# openssl rand -hex 32
# print("listdir:")
# print(os.listdir())
# Read the configuration file
config_file_loc = 'config.json'
with open(config_file_loc, 'r') as config_file:
    config = json.load(config_file)

SECRET_KEY = config['secret_key']
ALGORITHM = config['algorithm']
ACCESS_TOKEN_EXPIRE_MINUTES = config['account_token_expire_minutes']
DEFAULT_ADMIN_DICT = config['default_admin']


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    try:
        admin_user = crud.get_user_by_username(db, DEFAULT_ADMIN_DICT['username'])
        if not admin_user:
            crud.create_user(db, user=schemas.UserCreate(
                username=DEFAULT_ADMIN_DICT['username'],
                email=DEFAULT_ADMIN_DICT['email'],
                password=DEFAULT_ADMIN_DICT['password'],
                organization=DEFAULT_ADMIN_DICT['organization']
            ))
            # db.add()
            db.commit()
            # db.commit()
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

# TODO: make other non-db calls work like this!
def get_user(db, username: str):
    return crud.get_user_by_username(db, username)
    # if username in db:
        # user_dict = db[username]
        # return schemas.UserInDB(**user_dict)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not crud.verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)]
    ):
    # was current_user.disabled before
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
    ):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        print(f"db_user: {db_user}, already exists")
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def list_user_details(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db),
                    current_user: schemas.User = Depends(get_current_active_user)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return crud.delete_user(db, user_id=user_id)


@app.put("/users/{user_id}", response_model=schemas.User)
async def update_user_details(user_id: int, user_update: schemas.UserUpdate, 
                      current_user: Annotated[schemas.User, Depends(get_current_active_user)], 
                      db: Session = Depends(get_db)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return crud.update_user(db, user_id, user_update)


@app.put("/users/{user_id}/password", response_model=schemas.User)
def update_user_password(user_id: int, password_update: schemas.PasswordUpdate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not crud.verify_password(password_update.old_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return crud.update_user_password(db, user_id, password_update.new_password)


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
    ):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.post("/user/item/", response_model=schemas.Item)
def create_item_for_current_user(
    item: schemas.ItemCreate,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
    ):
    return crud.create_user_item(db=db, item=item, user_id=current_user.id)


@app.get("/items/", response_model=list[schemas.Item])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.post("/user/nosql_collections/", response_model=schemas.NoSQLCollection)
def create_nosql_collections_for_current_user(
    collection: schemas.NoSQLCollectionBase,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
    ):
    return crud.create_nosql_collection(db=db, collection=collection, user=current_user)


@app.get("/nosql_collections/", response_model=list[schemas.NoSQLCollection])
def list_nosql_collections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_nosql_collections(db, skip=skip, limit=limit)
    return items


@app.post("/user/projects/", response_model=schemas.Project)
def create_project_for_current_user(
    project: schemas.ProjectBase,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
    ):
    return crud.create_project(db=db, project=project, user=current_user)


@app.get("/projects/", response_model=list[schemas.Project])
def list_projects(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
                    db: Session = Depends(get_db), skip: int = 0, limit: int = 100
    ):

    return crud.get_projects(db=db, skip=skip, limit=limit)

@app.post("/user/workflows/", response_model=schemas.Workflow)
def create_workflow_for_current_user(
    workflow: schemas.WorkflowBase,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
    ):
    project = crud.get_project_by_id(db=db, id=workflow.project_id)
    # return f"Found project with name: {project.name} and ID: {project.id}"
    return crud.create_workflow(db=db, workflow=workflow, user=current_user, project=project)


@app.get("/workflows/", response_model=list[schemas.Workflow])
def list_workflows(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
                    db: Session = Depends(get_db), skip: int = 0, limit: int = 100
    ):

    return crud.get_workflows(db=db, skip=skip, limit=limit)

@app.get("/whoami/", response_model=schemas.User)
async def whoami(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)]
    ):
    return current_user
