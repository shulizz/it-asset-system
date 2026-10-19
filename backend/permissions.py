"""Permissions explicitly assigned per user by a super administrator."""

ALL_PERMISSIONS = [
    ("assets", "查看资产档案"),
    ("assets_write", "新增和编辑资产"),
    ("import", "导入数据"),
    ("export", "导出数据"),
    ("wechat", "管理微信账号（全部部门范围）"),
    ("wechat_read", "查看微信账号（全部账号）"),
    ("wechat_edit", "新增和编辑微信账号资料（全部账号）"),
    ("wechat_secret", "查看和修改微信密码"),
    ("apply", "提交设备申请"),
    ("scrap_apply", "提交报废申请"),
    ("transfer", "设备流转"),
    ("scrap", "报废管理"),
    ("approval", "审批中心"),
    ("reports", "报表统计"),
    ("idle", "空闲设备"),
    ("scrapped", "报废设备"),
    ("departments", "部门管理（全部部门范围）"),
    ("logs", "全局操作日志（全部部门范围）"),
]
PERMISSION_KEYS = {key for key, _ in ALL_PERMISSIONS}
GLOBAL_PERMISSIONS = {"departments", "logs", "wechat"}
PERMISSION_DEPENDENCIES = {"wechat_secret": {"wechat"}, "wechat_edit": {"wechat_read"}}


def module_permission(module):
    return "departments" if module == "department" else "wechat" if module == "wechat" else "assets"
