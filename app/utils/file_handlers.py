import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from app.core.config import settings

async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    try:
        file_location = os.path.join(destination, upload_file.filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(upload_file.file, file_object)
        return file_location
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.TEMPLATE_DIR, exist_ok=True)

def generate_job_id() -> str:
    return str(uuid.uuid4())

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

def is_supported_format(filename: str) -> bool:
    supported_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.txt'}
    return get_file_extension(filename) in supported_extensions