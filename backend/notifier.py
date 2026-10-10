"""邮件通知模块：发送医疗设备到期提醒邮件"""
import smtplib
import os
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from models import MedicalAsset

# ===== SMTP 配置（需要改成你自己的邮箱）=====
SMTP_HOST = os.environ.get('IT_ASSET_SMTP_HOST', 'smtp.qq.com')
SMTP_PORT = int(os.environ.get('IT_ASSET_SMTP_PORT', '465'))
SMTP_USER = os.environ.get('IT_ASSET_SMTP_USER', '')
SMTP_PASS = os.environ.get('IT_ASSET_SMTP_PASS', '')
SMTP_FROM = os.environ.get('IT_ASSET_SMTP_FROM', '')
# ==========================================

# 到期提醒接收人邮箱（逗号分隔）
def smtp_configured():
    return bool(SMTP_USER and SMTP_PASS)


def send_email(to_list: list, subject: str, content: str) -> dict:
    """发送邮件，返回 {success, message}"""
    if not SMTP_USER or not SMTP_PASS:
        return {"success": False, "message": "服务器尚未配置发件邮箱及SMTP授权码，请联系超级管理员完成配置"}
    if not to_list:
        return {"success": False, "message": "未配置接收人邮箱"}

    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM or SMTP_USER
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.attach(MIMEText(content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.login(SMTP_USER, SMTP_PASS)
            refused = server.sendmail(SMTP_USER, to_list, msg.as_string())
            if refused:
                return {"success": False, "message": f"部分邮箱投递失败：{len(refused)}个，请检查收件邮箱后重试"}
        return {"success": True, "message": f"已发送给 {len(to_list)} 个邮箱"}
    except Exception:
        return {"success": False, "message": "邮件发送失败，请检查发件邮箱授权码、SMTP服务和服务器网络"}


def get_expiring_medical(db: Session, days: int = 30, user=None) -> list:
    """获取 N 天内即将到期或已过期的医疗设备"""
    today = date.today()
    deadline = today + timedelta(days=days)
    query = db.query(MedicalAsset)
    if user is not None:
        from deps import scope_query
        query = scope_query(query, MedicalAsset, user)
    assets = query.filter(
        MedicalAsset.expiry_date.isnot(None),
        MedicalAsset.status.notin_(["scrapped", "archived"]),
    ).all()
    result = []
    for a in assets:
        try:
            exp = datetime.strptime(str(a.expiry_date)[:10], "%Y-%m-%d").date()
        except Exception:
            continue
        delta = (exp - today).days
        if delta <= days:
            result.append({
                "asset_number": a.asset_number,
                "name": a.name,
                "department": a.department or "",
                "keeper": a.keeper or "",
                "expiry_date": str(a.expiry_date)[:10],
                "days_left": delta,
            })
    result.sort(key=lambda x: x["days_left"])
    return result


def send_expiry_notice(db: Session, days: int = 30, recipients=None) -> dict:
    """发送到期提醒邮件"""
    expiring = get_expiring_medical(db, days)
    if not expiring:
        return {"success": True, "message": f"近{days}天内无设备到期，无需发送", "count": 0}

    rows = ""
    for e in expiring:
        e = {key: escape(str(value)) if key != 'days_left' else value for key, value in e.items()}
        if e["days_left"] < 0:
            tag = f'<span style="color:#dc2626;font-weight:bold">已过期{abs(e["days_left"])}天</span>'
        else:
            tag = f'<span style="color:#d97706;font-weight:bold">剩余{e["days_left"]}天</span>'
        rows += f"""
        <tr>
          <td style="padding:6px 12px;border:1px solid #e2e8f0">{e['asset_number']}</td>
          <td style="padding:6px 12px;border:1px solid #e2e8f0">{e['name']}</td>
          <td style="padding:6px 12px;border:1px solid #e2e8f0">{e['department']}</td>
          <td style="padding:6px 12px;border:1px solid #e2e8f0">{e['keeper']}</td>
          <td style="padding:6px 12px;border:1px solid #e2e8f0">{e['expiry_date']}</td>
          <td style="padding:6px 12px;border:1px solid #e2e8f0">{tag}</td>
        </tr>"""

    html = f"""
    <div style="font-family:'Microsoft YaHei',sans-serif;max-width:800px;margin:0 auto">
      <h2 style="color:#dc2626">医疗设备到期提醒</h2>
      <p>以下设备将在 <strong>{days} 天</strong>内到期或已过期，请及时处理：</p>
      <table style="border-collapse:collapse;width:100%;font-size:13px">
        <thead>
          <tr style="background:#f8fafc">
            <th style="padding:8px 12px;border:1px solid #e2e8f0">资产编号</th>
            <th style="padding:8px 12px;border:1px solid #e2e8f0">设备名称</th>
            <th style="padding:8px 12px;border:1px solid #e2e8f0">科室</th>
            <th style="padding:8px 12px;border:1px solid #e2e8f0">保管人</th>
            <th style="padding:8px 12px;border:1px solid #e2e8f0">到期日期</th>
            <th style="padding:8px 12px;border:1px solid #e2e8f0">状态</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#94a3b8;font-size:12px;margin-top:16px">此邮件由固定资产管理系统自动发送</p>
    </div>
    """
    subject = f"【到期提醒】{len(expiring)}台医疗设备{days}天内到期"
    result = send_email(recipients or [], subject, html)
    result["count"] = len(expiring)
    return result
