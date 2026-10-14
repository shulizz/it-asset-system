# 域名入口

访问地址：https://slzz.cloud 。`www.slzz.cloud` 自动跳转到根域名，HTTP 自动跳转 HTTPS。

服务器目录：`C:\FixedAssetSystem\gateway`，对应固定资产管理系统项目内的 `gateway` 文件夹。

- Windows 服务：`FixedAssets-Gateway`，开机启动，异常退出自动重启。
- 后端启动任务：`IT-Asset-System`，运行时间上限已改为无限。
- Caddy 版本：2.11.7，官方 Windows amd64 发布包经 SHA512 校验后安装。
- 外部 TCP 80、443 转发到本机后端 `127.0.0.1:8000`。
- 配置：`Caddyfile`；证书及续期状态：`data`；运行日志：`logs`。
- 证书和日志目录不提交 Git。旧 IP 端口入口仍保留。

修改配置后，在服务器管理员 PowerShell 中执行：

```powershell
& 'C:\FixedAssetSystem\gateway\caddy.exe' validate --config 'C:\FixedAssetSystem\gateway\Caddyfile' --adapter caddyfile
& 'C:\FixedAssetSystem\gateway\caddy.exe' reload --config 'C:\FixedAssetSystem\gateway\Caddyfile' --adapter caddyfile
```

DNS 的根域名和 www A 记录指向服务器公网 IP；腾讯云及 Windows 防火墙应放行 TCP 80、443。Caddy 负责证书申请和自动续期，需保留其 data 目录及公网验证端口。

官方维护文档：https://caddyserver.com/docs/running
