import logging
import os

from database import Base, SessionLocal, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from models import Department, Role, User
from passlib.context import CryptContext
from routers import (
    assets,
    auth,
    backup,
    delete_req,
    departments,
    import_export,
    logs,
    reports,
    scrap,
    transfer,
    user_import,
    version,
    wechat,
)

Base.metadata.create_all(bind=engine)

from migrations import migrate_schema

migrate_schema(engine)

app = FastAPI(title="IT资产管理系统 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # API authentication uses explicit Bearer tokens, not browser cookies.
    allow_credentials=False,
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
app.include_router(reports.router)
app.include_router(user_import.router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    first_boot = not db.query(User).first()
    if first_boot:
        bootstrap_password = os.getenv("IT_ASSET_BOOTSTRAP_PASSWORD")
        if not bootstrap_password:
            db.close()
            raise RuntimeError(
                "IT_ASSET_BOOTSTRAP_PASSWORD must be set when creating the first user"
            )
        admin = User(
            username=os.getenv("IT_ASSET_BOOTSTRAP_USERNAME", "admin"),
            password_hash=pwd_context.hash(bootstrap_password),
            name="管理员",
            role="super_admin",
            department="IT部",
            is_active=1,
        )
        db.add(admin)
        db.commit()
    if first_boot and not db.query(Department).first():
        for name in ["IT部", "研发部", "市场部", "财务部", "行政部", "管理层"]:
            db.add(Department(name=name))
        db.commit()
    import json

    from deps import get_user_permissions

    for user in db.query(User).filter(User.permissions.is_(None)).all():
        # Preserve legacy grants once; runtime access never depends on a role template.
        legacy_role = (
            db.get(Role, user.role_id)
            if user.role_id
            else db.query(Role).filter(Role.name == user.role).first()
        )
        from permissions import PERMISSION_KEYS

        try:
            legacy = (
                json.loads(legacy_role.permissions)
                if legacy_role and legacy_role.permissions
                else []
            )
            grants = (
                sorted(PERMISSION_KEYS.intersection(p for p in legacy if isinstance(p, str)))
                if isinstance(legacy, list)
                else []
            )
        except (ValueError, TypeError):
            grants = []
        user.permissions = json.dumps(
            get_user_permissions(user, db) if user.role == "super_admin" else grants
        )
        if user.department and not user.department_id:
            department = db.query(Department).filter(Department.name == user.department).first()
            user.department_id = department.id if department else None
    db.commit()
    from routers.backup import do_backup

    try:
        do_backup()
    except Exception:
        logging.getLogger(__name__).exception("Startup database backup failed")
    finally:
        db.close()


frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")


@app.get("/")
def index():
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")
    if os.path.exists(f):
        return FileResponse(f)
    return {"status": "ok", "app": "IT资产管理系统"}


@app.get("/{full_path:path}")
def spa(full_path: str):
    idx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"status": "ok"}
