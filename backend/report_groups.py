"""Hospital/network report totals share the same scope and module access as exports."""

from deps import can_view_fire, can_view_medical, get_user_permissions, scope_query
from models import Department
from sqlalchemy import func

HOSPITAL_DEPARTMENTS = {"护理部", "医院", "门诊", "办公室"}


def group_summary(db, user, module_config):
    modules = ["it", "phone", "number"]
    if can_view_medical(user):
        modules.append("medical")
    if can_view_fire(user):
        modules.append("fire")
    groups = [
        {"key": "hospital", "name": "医院", "counts": dict.fromkeys(modules, 0)},
        {"key": "network", "name": "网络部", "counts": dict.fromkeys(modules, 0)},
    ]
    unassigned = dict.fromkeys(modules, 0)
    for module in modules:
        model = module_config[module]["model"]
        department = func.coalesce(Department.name, model.department)
        quantity = func.sum(model.quantity) if module == "phone" else func.count(model.id)
        rows = (
            scope_query(db.query(model), model, user)
            .outerjoin(Department, Department.id == model.department_id)
            .with_entities(department, quantity)
            .group_by(department)
            .all()
        )
        for department_name, count in rows:
            department_name = (department_name or "").strip()
            if not department_name:
                unassigned[module] += int(count or 0)
            else:
                index = 0 if department_name in HOSPITAL_DEPARTMENTS else 1
                groups[index]["counts"][module] += int(count or 0)
    permissions = get_user_permissions(user, db)
    can_wechat = "wechat_read" in permissions or (
        "wechat" in permissions and (user.role == "super_admin" or user.data_scope == "all")
    )
    wechat_count = db.query(module_config["wechat"]["model"]).count() if can_wechat else None
    return {
        "modules": [{"key": key, "label": module_config[key]["label"]} for key in modules],
        "groups": groups,
        "unassigned": unassigned,
        "wechat_count": wechat_count,
        "hospital_departments": sorted(HOSPITAL_DEPARTMENTS),
        "scope": "all"
        if user.role == "super_admin" or user.data_scope in {"all", "all_read_dept_write"}
        else "department",
    }
