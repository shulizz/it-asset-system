"""Hospital/network report totals share the same scope and module access as exports."""

from deps import can_view_fire, can_view_medical, get_user_permissions, scope_query
from models import Department
from sqlalchemy import func

HOSPITAL_DEPARTMENTS = {"护理部", "医院", "门诊", "办公室"}


def it_scrap_category(name, category):
    name, category = (name or "").strip(), (category or "").strip()
    if "显示器" in name or category == "显示器":
        return "monitors"
    if "主机" in name or category == "台式机" or name == "台式机":
        return "hosts"
    return "other"


def group_summary(db, user, module_config):
    modules = ["it", "phone", "number"]
    if can_view_medical(user):
        modules.append("medical")
    if can_view_fire(user):
        modules.append("fire")

    def tally():
        return {
            "counts": dict.fromkeys(modules, 0),
            "scrapped": dict.fromkeys(modules, 0),
            "it_scrapped": {"hosts": 0, "monitors": 0, "other": 0},
        }

    groups = [
        {"key": "hospital", "name": "医院", **tally()},
        {"key": "network", "name": "网络部", **tally()},
    ]
    unassigned = tally()
    for module in modules:
        model = module_config[module]["model"]
        department = func.coalesce(Department.name, model.department)
        quantity = func.sum(model.quantity) if module == "phone" else func.count(model.id)
        dimensions = [department, model.status]
        if module == "it":
            dimensions.extend([model.name, model.category])
        rows = (
            scope_query(db.query(model), model, user)
            .outerjoin(Department, Department.id == model.department_id)
            .with_entities(*dimensions, quantity)
            .group_by(*dimensions)
            .all()
        )
        for row in rows:
            department_name, status, *details = row[:-1]
            count = int(row[-1] or 0)
            department_name = (department_name or "").strip()
            if not department_name:
                target = unassigned
            else:
                index = 0 if department_name in HOSPITAL_DEPARTMENTS else 1
                target = groups[index]
            target["scrapped" if status == "scrapped" else "counts"][module] += count
            if status == "scrapped" and module == "it":
                target["it_scrapped"][it_scrap_category(*details)] += count
    permissions = get_user_permissions(user, db)
    can_wechat = "wechat_read" in permissions or (
        "wechat" in permissions and (user.role == "super_admin" or user.data_scope == "all")
    )
    wechat_model = module_config["wechat"]["model"]
    wechat_count = (
        db.query(wechat_model).filter(wechat_model.status.notin_(["scrapped", "archived"])).count()
        if can_wechat
        else None
    )
    return {
        "modules": [{"key": key, "label": module_config[key]["label"]} for key in modules],
        "groups": groups,
        "unassigned": unassigned["counts"],
        "unassigned_scrapped": unassigned["scrapped"],
        "unassigned_it_scrapped": unassigned["it_scrapped"],
        "it_scrapped_totals": {
            key: sum(group["it_scrapped"][key] for group in [*groups, unassigned])
            for key in ["hosts", "monitors", "other"]
        },
        "wechat_count": wechat_count,
        "hospital_departments": sorted(HOSPITAL_DEPARTMENTS),
        "scope": "all"
        if user.role == "super_admin" or user.data_scope in {"all", "all_read_dept_write"}
        else "department",
    }
