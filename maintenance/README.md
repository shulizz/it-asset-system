# 服务器维护

正式入口：https://slzz.cloud 。服务器项目为 `C:\固定资产管理系统`，英文别名 `C:\FixedAssetSystem`。

管理员 PowerShell 使用 `maintenance/manage-system.ps1 -Action Status|Start|Stop|Restart` 管理后端计划任务。脚本只处理本系统任务及经核对的后端端口进程，不按名称终止全部 Python 程序。HTTPS 网关由 `FixedAssets-Gateway` Windows 服务管理。

计划任务执行 `maintenance/runtime/start-fixed-assets.ps1`，读取机器环境变量中的签名密钥和 SMTP 配置，后端仅监听 `127.0.0.1:8000`，代理头只信任本机 Caddy。浏览器和客户端统一使用 HTTPS 域名，旧 IP 地址及旧 ngrok 配置应切换。

只读检查数据库：

```powershell
& C:\FixedAssetSystem\backend\.venv\Scripts\python.exe C:\FixedAssetSystem\maintenance\check_database.py --database C:\FixedAssetSystem\backend\it_assets.db
```

检查脚本不导入应用、不迁移、不改记录，只输出完整性、关联异常数量和各表记录数。不要把数据库、备份、真实密钥、邮箱授权码或检查中的业务资料提交 Git。

旧的全进程重启、旧目录启动、一次性源码修补、无保护清库及直连真实服务的测试脚本已退出发行范围，可在 Git 历史追溯。清空、恢复或结构迁移应另行制定包含备份和核对的步骤。

发布前运行后端测试和前端测试、构建；备份数据库及待覆盖/删除的代码，再部署并核对原业务记录。发布清单应包含 Git 中已删除文件，避免旧脚本留在服务器运行目录。原型 HTML 与截图作为设计档案保留，不复制到生产目录。
