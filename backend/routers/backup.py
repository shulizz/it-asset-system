import os, shutil, glob
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from deps import require_super_admin

router = APIRouter(prefix="/api/backup", tags=["backup"])

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "it_assets.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def do_backup():
    name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    path = os.path.join(BACKUP_DIR, name)
    shutil.copy2(DB_PATH, path)
    # 只保留最近20个备份
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.db")))
    for f in files[:-20]:
        os.remove(f)
    return name

@router.post("/")
def backup_now(user = Depends(require_super_admin)):
    name = do_backup()
    return {"ok": True, "file": name}

@router.get("/list")
def list_backups(user = Depends(require_super_admin)):
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.db")), reverse=True)
    return [{"name": os.path.basename(f), "size": os.path.getsize(f)} for f in files]

@router.get("/download/{name}")
def download(name: str, user = Depends(require_super_admin)):
    path = os.path.join(BACKUP_DIR, name)
    return FileResponse(path, filename=name)
