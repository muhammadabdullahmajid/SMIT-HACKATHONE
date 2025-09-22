from agents import Agent, OpenAIChatCompletionsModel, ModelSettings, Runner,function_tool
from openai import AsyncOpenAI
from config.database import get_db
from pymongo import MongoClient
import os
from dotenv import load_dotenv       
from typing import Any
from model.pydantic_model import add_stuedent

load_dotenv()


db = get_db()
collection = db["students"]

print("Client is:", db)


@function_tool
def read_students():
    print("Fetching all students...")
    """Fetch all students from the database.
    Returns:
        dict: A dictionary containing the list of students and any error message.
    Args:
        None
    
        """
    try:
        students = collection.find({})
        students_list = []
        for stud in students:
            stud["_id"] = str(stud["_id"])  # Convert ObjectId to string
            students_list.append(stud)
        print("Students fetched:", students_list)    

        return {
            "Data": students_list,
            "Error": False,
            "Message": "All students data fetched successfully"
        }
    except Exception as e:
        return {
            "Data": [],
            "Error": True,
            "Message": str(e)
        }


#for one student
@function_tool
def read_student_by_id(id: int):
        print("Fetching student by name...")
        """Fetch a student by name from the database.
        Args:
            name (str): The name of the student to fetch.
        Returns:
            dict: A dictionary containing the student data and any error message.
        """
        try:
            student = collection.find_one({"id": id})
            if student:
                student["_id"] = str(student["_id"])  # Convert ObjectId to string
                return {
                    "Data": student,
                    "Error": False,
                    "Message": "Student data fetched successfully"
                }
            else:
                return {
                    "Data": {},
                    "Error": True,
                    "Message": "Student not found"
                }

        except Exception as e:
            return {
                "Data": {},
                "Error": True,
                "Message": str(e)
            }

#for add student
@function_tool
def add_student(id:int,name:str,email:str,department:str):
    print("Adding student...")
    """Add a new student to the database.
    Args:
        add (add_stuedent): An instance of the add_stuedent model containing student details.
        name: str - The name of the student.
        id: int - The numeric ID of the student.
        email: str - The email address of the student.
    Returns:
        dict: A dictionary containing the result of the insertion operation.
    """
    try:
        result = collection.insert_one({
            "name": name, 
            "id": id, 
            "email": email, 
            "department": department
            })
        print("Student added:", result.inserted_id)
        return {
            "Data": {"id": str(result.inserted_id)},
            "Error": False,
            "Message": "Student added successfully"
        }
    except Exception as e:
        return {
            "Data": {},
            "Error": True,
            "Message": str(e)
        }
    except Exception as e:
        return {
            "Data": {},
            "Error": True,
            "Message": str(e)
        }




@function_tool
def delete_student(id: int):
    print("Deleting student...")
    """"    Delete a student by name.
        Args:
            name (str): The name of the student to delete.
        Returns:
            dict: A dictionary containing the result of the deletion operation.

    """
    try:
        result = collection.delete_one({"id": id})
        if result.deleted_count > 0:
            return {
                "Data": {"id": id},
                "Error": False,
                "Message": "Student deleted successfully"
            }
        else:
            return {
                "Data": {},
                "Error": True,
                "Message": "Student not found"
            }
    except Exception as e:
        return {
            "Data": {},
            "Error": True,
            "Message": str(e)
        }
    


 
@function_tool
def update_student(id: int, field: str, new_value: Any):
    print("Updating student...")

    """
    Update a single field for a student identified by `id`.

    Args:
        id (int): The student's numeric id (not Mongo _id).
        field (str): The field/column to update (e.g., "name", "age", "grade", "department", "email").
        new_value (Any): The new value to set.

    Returns:
        dict: Result payload with success/error info.
    """

    try:
        
        if field in ["_id"]:
            return {
                "Data": {},
                "Error": True,
                "Message": "Updating '_id' is not allowed"
            }

        # Whitelist the fields your app actually uses
        allowed_fields = {"id", "name", "age", "grade", "department", "email"}
        if field not in allowed_fields:
            return {
                "Data": {},
                "Error": True,
                "Message": f"Invalid field '{field}'. Allowed: {sorted(list(allowed_fields))}"
            }

        # Optional casting for numeric fields
        if field in {"age", "id"}:
            try:
                new_value = int(new_value)
            except (TypeError, ValueError):
                return {
                    "Data": {},
                    "Error": True,
                    "Message": f"Field '{field}' must be an integer"
                }

        # Build the update
        update_doc = {"$set": {field: new_value}}

        # Match by your custom integer id (NOT Mongo _id)
        result = collection.update_one({"id": id}, update_doc)

        if result.matched_count == 0:
            return {
                "Data": {},
                "Error": True,
                "Message": f"Student with id={id} not found"
            }

        # Optionally fetch the updated doc to return
        updated = collection.find_one({"id": id})
        if updated:
            updated["_id"] = str(updated["_id"])

        return {
            "Data": {"before_id": id, "updated_field": field, "new_value": new_value, "student": updated},
            "Error": False,
            "Message": "Student updated successfully"
        }

    except Exception as e:
        return {
            "Data": {},
            "Error": True,
            "Message": str(e)
        }
