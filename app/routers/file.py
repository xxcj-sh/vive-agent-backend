from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """文件上传"""
    import os
    import uuid
    from datetime import datetime
    from pathlib import Path
    
    try:
        # Debug logging
        print(f"Upload request received - filename: {file.filename}, type: {type}")
        print(f"Current user: {current_user}")
        
        # Configure upload directory
        UPLOAD_DIR = Path("uploads")
        UPLOAD_DIR.mkdir(exist_ok=True)
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file type
        ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create user-specific directory - handle different user ID formats
        user_id = getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None) or 'anonymous'
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(exist_ok=True)
        
        file_path = user_dir / unique_filename
        
        # Save file
        import shutil
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return file URL that can be accessed via the static files mount
        file_url = f"/uploads/{user_id}/{unique_filename}"
        
        return BaseResponse(
            code=0, 
            message="success", 
            data={
                "url": file_url,
                "filename": unique_filename,
                "original_filename": file.filename,
                "upload_time": datetime.now().isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")