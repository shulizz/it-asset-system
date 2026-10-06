from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/api/version", tags=["version"])

CURRENT_VERSION = "1.2.3"

@router.get("")
def get_version():
    return {"version": CURRENT_VERSION, "download_url": "/api/version/download"}

@router.get("/download")
def download_client():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client.zip")
    if os.path.exists(path):
        return FileResponse(path, filename="client.zip")
    return {"error": "未上传"}
