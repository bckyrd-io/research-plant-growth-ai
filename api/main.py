from fastapi import FastAPI, UploadFile, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session  # Add this import
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from jose import JWTError, jwt
from capture import capture_and_save_image
from users import create_user, get_user_by_username, UserRoleEnum, hash_password
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from users import authenticate_user, get_current_user
from models import SessionLocal, User  # Add this import

app = FastAPI()

# Configure CORS
origins = ["*"]  # Update with the origin of your web page
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... Other middleware and configuration ...

# Endpoint to capture and save images
@app.post("/capture")
async def capture_image(file: UploadFile = UploadFile(...)):
    return capture_and_save_image(file)

# Registration endpoint
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[UserRoleEnum] = UserRoleEnum.user

@app.post("/register")
async def register_user(user: UserCreate):
    user_data = user.dict()
    user_data["hashed_password"] = hash_password(user.password)
    del user_data["password"]
    return create_user(user_data)

# Login endpoint
@app.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_token = await authenticate_user(form_data.username, form_data.password)
    if user_token is None:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password")
    return user_token

# Edit user role endpoint (Requires admin privileges)
@app.put("/user/{user_id}/edit-role")
async def edit_user_role(user_id: int, new_role: UserRoleEnum, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == current_user).first()
    db.close()

    if user.role != UserRoleEnum.admin:
        raise HTTPException(
            status_code=403, detail="Only admin users can edit roles")

    db = SessionLocal()
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    db_user.role = new_role
    db.commit()
    db.close()

    return {"message": "User role updated successfully"}

# Delete user endpoint (Requires admin privileges)
@app.delete("/user/{user_id}/delete")
async def delete_user(user_id: int, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == current_user).first()
    db.close()

    if user.role != UserRoleEnum.admin:
        raise HTTPException(
            status_code=403, detail="Only admin users can delete users")

    db = SessionLocal()
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    db.close()

    return {"message": "User deleted successfully"}

# ... Define other endpoints and dependencies as needed ...