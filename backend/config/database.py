from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    try:    
        print("Connecting mongoDB")  
        print("MONGODB_URI:", DATABASE_URL)  # Debugging line to check the URI

        client = MongoClient(DATABASE_URL)
        print("Connected to MongoDB",DATABASE_URL)
        db=client["students_record"] # <-- specify your database name here
        return db

    except Exception as e:
        print("Error connecting to MongoDB:", e)
        return None
    

# def get_db_client():
#     try:
#         client = MongoClient(db_url)
#         print("Connected to MongoDB")
#         return client
#     except Exception as e:
#         print("Error connecting to DB:", e)
#     return None

# db_client = get_db_client()

# def get_collection():
#     db = db_client.get_database("students_record")
#     collection = db.get_collection("students")
#     return collection