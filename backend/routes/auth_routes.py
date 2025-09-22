from fastapi import APIRouter, Depends, HTTPException
from pymongo.collection import Collection
from config.database import get_db   # <-- should return MongoDB database
from utils.auth_utils import create_access_token, hash_password, verify_api_key, verify_password,verify_access_token
from model.pydantic_model import LoginUser, UserCreate,ResetPasswordRequest
from bson import ObjectId

auth = APIRouter()

@auth.post("/register")
def create_user(user: UserCreate, db=Depends(get_db)):
    try:
        users_collection: Collection = db["signup"]   # <-- changed to signup

        if users_collection.find_one({"email": user.email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        user_hash_password = hash_password(user.password)
        user_doc = {
            "name": user.name,
            "email": user.email,
            "password": user_hash_password,
        }
        result = users_collection.insert_one(user_doc)
        db_user = users_collection.find_one({"_id": result.inserted_id})

        token = create_access_token(
            data={"email": db_user["email"], "name": db_user["name"], "user_id": str(db_user["_id"])}
        )

        return {"data": {"name": db_user["name"], "email": db_user["email"], "token": token},
                "message": "User registered and login successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e), "status": "error", "data": None}


@auth.post("/login", dependencies=[Depends(verify_api_key)])
def login_user(user: LoginUser, db=Depends(get_db)):
    try:
        users_collection: Collection = db["signup"]   

        db_user = users_collection.find_one({"email": user.email})
        if not db_user:
            raise HTTPException(status_code=404, detail="Email not found")

        is_valid_password = verify_password(user.password, db_user["password"])
        if not is_valid_password:
            raise HTTPException(status_code=401, detail="Invalid password")

        token = create_access_token(
            data={"email": db_user["email"], "name": db_user["name"], "user_id": str(db_user["_id"])}
        )

        return {"data": {"name": db_user["name"], "email": db_user["email"], "token": token},
                "message": "User logged in successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e), "status": "error", "data": None}




@auth.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db=Depends(get_db)):
    users_collection: Collection = db["signup"]

    # normalize email to lowercase & strip spaces
    email = request.email.strip().lower()

    user = users_collection.find_one({"email": email})
    if not user:
        # 👀 debug print to see what’s really inside DB
        all_users = list(users_collection.find({}, {"email": 1}))
        raise HTTPException(
            status_code=404,
            detail=f"Email not found. Provided={email}, Existing={all_users}"
        )

    hashed_pw = hash_password(request.new_password)
    result = users_collection.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"password": hashed_pw}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Password update failed")

    return {
        "message": f"Password has been reset for {email}",
        "status": "success"
    }

@auth.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db=Depends(get_db)):
    users_collection: Collection = db["signup"]

    # normalize email to lowercase & strip spaces
    email = request.email.strip().lower()

    user = users_collection.find_one({"email": email})
    if not user:
        # 👀 debug print to see what’s really inside DB
        all_users = list(users_collection.find({}, {"email": 1}))
        raise HTTPException(
            status_code=404,
            detail=f"Email not found. Provided={email}, Existing={all_users}"
        )

    hashed_pw = hash_password(request.new_password)
    result = users_collection.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"password": hashed_pw}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Password update failed")

    return {
        "message": f"Password has been reset for {email}",
        "status": "success"
    }
