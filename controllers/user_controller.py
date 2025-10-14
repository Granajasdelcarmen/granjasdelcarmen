from fastapi import HTTPException
from database.supabase import supabase
from schemas.user_schema import UserBase  

# Create a user
def create_user(user: UserBase):
    try:
        data = supabase.table("users").insert({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "email": user.email,
            "password": user.password
        }).execute()
        return {
            "message": "User created successfully",
            "user": data.data[0] if data.data else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {e}")

# Get all users
def list_users():
    try:
        data = supabase.table("users").select("*").execute()
        return data.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {e}")

# Get a user by ID
def get_user(id: int):
    try:
        data = supabase.table("users").select("*").eq("id", id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="User not found")
        return data.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {e}")

# Delete a user
def delete_user(id: int):
    try:
        data = supabase.table("users").delete().eq("id", id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {e}")
