from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from database import engine, SessionLocal, Base
from models import User, Department
from passlib.context import CryptContext
from routers import auth, assets, transfer, scrap, delete_req, logs, departments, backup, version, wechat, import_export

Base.metadata.create_all(bind=engine)

from sqlalchemy import text
with engine.connect() as conn:
    for col in ['new_user VARCHAR(50)', 'new_dept VARCHAR(50)', 'model VARCHAR(100)', 'notes VARCHAR(500)']:
        try:
            conn.execute(text(f"ALTER TABLE it_assets ADD COLUMN {col}"))
            conn.commit()
        except: pass

app = FastAPI(title="IT资产管理系统 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(transfer.router)
app.include_router(scrap.router)
app.include_router(delete_req.router)
app.include_router(logs.router)
app.include_router(departments.router)
app.include_router(backup.router)
app.include_router(version.router)
app.include_router(wechat.router)
app.include_router(import_export.router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            name="管理员",
            role="super_admin",
            department="IT部",
            is_active=1
        )
        db.add(admin)
        db.commit()
    if not db.query(Department).first():
        for name in ["IT部", "研发部", "市场部", "财务部", "行政部", "管理层"]:
            db.add(Department(name=name))
        db.commit()
    from routers.backup import do_backup
    try: do_backup()
    except: pass
    db.close()

frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

@app.get("/")
def index():
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")
    if os.path.exists(f): return FileResponse(f)
    return {"status": "ok", "app": "IT资产管理系统"}

@app.get("/{full_path:path}")
def spa(full_path: str):
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", full_path)
    if os.path.exists(f) and os.path.isfile(f): return FileResponse(f)
    idx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")
    if os.path.exists(idx): return FileResponse(idx)
    return {"status": "ok"}

