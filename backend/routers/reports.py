from datetime import date

from database import get_db
from deps import can_view_fire, can_view_medical, get_user_permissions, require_perm, scope_query
from excel_output import append_text_row, export_workbook, workbook_response
from fastapi import APIRouter, Depends, HTTPException
from report_groups import group_summary
from sqlalchemy.orm import Session

from routers.import_export import MODULES

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/group-summary")
def report_group_summary(db: Session = Depends(get_db), user=Depends(require_perm("reports"))):
    return group_summary(db, user, MODULES)


@router.get("/export")
def export_report(db: Session = Depends(get_db), user=Depends(require_perm("reports"))):
    permissions = get_user_permissions(user, db)
    if "export" not in permissions:
        raise HTTPException(403, "没有导出权限")
    with export_workbook() as wb:
        modules = ["it", "phone"]
        if can_view_fire(user):
            modules.append("fire")
        if can_view_medical(user):
            modules.append("medical")
        modules.append("number")
        if "wechat_read" in permissions or (
            "wechat" in permissions and (user.role == "super_admin" or user.data_scope == "all")
        ):
            modules.append("wechat")
        distribution = {}
        for module in modules:
            cfg = MODULES[module]
            model = cfg["model"]
            query = (
                scope_query(db.query(model), model, user)
                if hasattr(model, "department_id")
                else db.query(model)
            )
            fields = [field for field in cfg["fields"] if field[1] != "wx_password"]
            rows = query.with_entities(*(getattr(model, field[1]) for field in fields)).yield_per(
                500
            )
            department_index = next(
                (index for index, field in enumerate(fields) if field[1] == "department"), None
            )
            ws = wb.create_sheet(cfg["label"])
            ws.append([field[0] for field in fields])
            for row in rows:
                append_text_row(ws, list(row))
                if module != "wechat":
                    key = row[department_index] or "未分配部门"
                    distribution.setdefault(
                        key, dict.fromkeys(["it", "phone", "fire", "medical", "number"], 0)
                    )[module] += (
                        row[
                            next(
                                index
                                for index, field in enumerate(fields)
                                if field[1] == "quantity"
                            )
                        ]
                        if module == "phone"
                        else 1
                    )
        ws = wb.create_sheet("部门统计")
        statistic_modules = [module for module in modules if module != "wechat"]
        ws.append(["部门"] + [MODULES[module]["label"] for module in statistic_modules])
        for department, counts in sorted(distribution.items()):
            append_text_row(ws, [department] + [counts[module] for module in statistic_modules])
        summary = group_summary(db, user, MODULES)
        ws = wb.create_sheet("医院网络部统计")
        keys = [module["key"] for module in summary["modules"]]
        append_text_row(ws, ["分组"] + [module["label"] for module in summary["modules"]])
        for group in summary["groups"]:
            append_text_row(ws, [group["name"]] + [group["counts"][key] for key in keys])
        append_text_row(
            ws, ["未分配部门（未计入两组）"] + [summary["unassigned"][key] for key in keys]
        )
        append_text_row(ws, ["医院范围：护理部、医院、门诊、办公室；网络部范围：其余部门。"])
        append_text_row(
            ws, ["按可查看范围统计现有台账，含已报废，不含已移出档案；手机按实际台数。"]
        )
        if summary["wechat_count"] is not None:
            append_text_row(
                ws, ["微信账号未设置部门，不分组；可查看账号总数", summary["wechat_count"]]
            )
        filename = f"资产报表_{date.today()}.xlsx"
        return workbook_response(wb, filename)
