# IT固定资产管理系统

一个轻量级的企业IT设备固定资产管理系统，适用于医院、公司等组织。

## 功能模块

- **IT设备档案管理**：设备录入、编辑、归档，自动生成资产编号
- **手机设备管理**：手机设备档案管理
- **医疗设备管理**：医疗设备档案管理
- **电话号码管理**：运营商、主副卡、使用人、状态（注销/不再使用）
- **微信账号管理**：微信账号、密码、实名人、使用人、用途
- **设备流转管理**：领用、归还、部门调拨、离职回收，自动更新设备状态
- **报废管理**：报废申请、审批、归档，通过后设备自动标记为已报废
- **删除审批**：所有删除需走审批流程，管理员/超级管理员审批
- **部门管理**：部门档案，设备按部门归类
- **用户管理**：多角色（超级管理员、资产管理员、部门主管）
- **报表统计**：设备台账、部门统计、闲置清单，支持导出Excel
- **操作日志**：所有操作全程留痕
- **自动备份**：数据库定时备份

## 技术栈

- **后端**：Python FastAPI + SQLite
- **前端**：Vue 3 + Vite
- **桌面客户端**：Electron（免安装版）
- **部署**：Windows服务器 + 内网穿透（ngrok/cpolar/cloudflared）

## 快速启动

### 后端
```bash
set IT_ASSET_SECRET_KEY=请设置高强度随机密钥
set IT_ASSET_BOOTSTRAP_PASSWORD=首次部署时的管理员密码
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

`IT_ASSET_SECRET_KEY` 是必填项。只有数据库尚无用户时才需要
`IT_ASSET_BOOTSTRAP_PASSWORD`，首次管理员创建完成后应删除该环境变量。

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 构建桌面客户端
```bash
npm run build
# 然后将 dist/ 内容拷贝到 Electron 运行时 resources/app/
```

## 截图

（待添加）
