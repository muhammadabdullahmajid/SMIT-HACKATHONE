from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from config.database import get_db
from utils.auth_utils import get_current_user
import asyncio

students_router = APIRouter()

def fetch_students_data():
    """Regular function to fetch students data from database"""
    try:
        db = get_db()
        collection = db["students"]
        
        students = collection.find({})
        students_list = []
        for stud in students:
            stud["_id"] = str(stud["_id"])  # Convert ObjectId to string
            students_list.append(stud)
        
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

@students_router.get("/test")
async def test_endpoint():
    """Test endpoint to check if the router is working"""
    return {"message": "Students router is working", "status": "success"}

@students_router.get("/test-auth")
async def test_auth_endpoint(current_user: dict = Depends(get_current_user)):
    """Test endpoint to check if authentication is working"""
    return {
        "message": "Authentication is working", 
        "status": "success",
        "user_id": current_user.get("user_id", "unknown")
    }

@students_router.get("/students")
async def get_all_students(current_user: dict = Depends(get_current_user)):
    """Get all students for dashboard display"""
    try:
        print(f"Getting students for user: {current_user.get('user_id', 'unknown')}")
        
        # Use the regular function to fetch students
        result = fetch_students_data()
        print(f"Read students result: {result}")
        
        if result.get("Error", False):
            error_msg = result.get("Message", "Failed to fetch students")
            print(f"Error in read_students: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        students_data = result.get("Data", [])
        print(f"Found {len(students_data)} students")
        
        return {
            "Data": students_data,
            "total": len(students_data),
            "message": "Students fetched successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in get_all_students: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching students: {str(e)}")

@students_router.get("/students/stats")
async def get_student_stats(current_user: dict = Depends(get_current_user)):
    """Get student statistics for dashboard"""
    try:
        # Get all students
        result = fetch_students_data()
        
        if result.get("Error", False):
            raise HTTPException(status_code=500, detail=result.get("Message", "Failed to fetch students"))
        
        students_data = result.get("Data", [])
        
        # Calculate statistics
        total_students = len(students_data)
        
        # Department distribution
        departments = {}
        for student in students_data:
            dept = student.get("department", "Unknown")
            departments[dept] = departments.get(dept, 0) + 1
        
        # Recent students (last 5)
        recent_students = students_data[-5:] if len(students_data) > 5 else students_data
        
        return {
            "total_students": total_students,
            "departments": departments,
            "recent_students": recent_students,
            "department_count": len(departments)
        }
        
    except Exception as e:
        print(f"Error in get_student_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching student stats: {str(e)}")
