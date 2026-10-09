import os, sqlite3, glob, re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from deps import require_super_admin
from database import engine

router = APIRouter(prefix="/api/backup", tags=["backup"])

DB_PATH = os.path.abspath(engine.url.database)
BACKUP_DIR = os.getenv('IT_ASSET_BACKUP_DIR', os.path.join(os.path.dirname(DB_PATH), 'backups'))
os.makedirs(BACKUP_DIR, exist_ok=True)

def do_backup():
    name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    path = os.path.join(BACKUP_DIR, name)
    with sqlite3.connect(DB_PATH) as source, sqlite3.connect(path) as target:
        source.backup(target)
        if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('备份完整性检查失败')
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
    if not re.fullmatch(r'backup_\d{8}_\d{6}\.db', name):
        raise HTTPException(400, '无效备份文件名')
    path = os.path.join(BACKUP_DIR, name)
    if not os.path.isfile(path):
        raise HTTPException(404, '备份不存在')
    return FileResponse(path, filename=name)
