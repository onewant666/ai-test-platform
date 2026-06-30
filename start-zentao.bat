@echo off
echo ==========================================
echo   启动 ZenTao Box
echo ==========================================
echo.
echo 注意:
echo   - 需要以管理员身份运行
echo   - ZenTao Apache 默认端口 80 (如被占用自动尝试 8999)
echo   - ZenTao MySQL 端口 3306 (如被占用自动尝试 3999)
echo   - 请确保端口 3306 没有其他 MySQL 实例运行
echo.
echo 启动后访问: http://localhost:80 (或 http://localhost:8999)
echo 管理员账号: admin / 123456 (首次登录需修改密码)
echo.
echo 按任意键启动...
pause > nul
start "" "C:\ZenTao\ZenTao.exe"
echo ZenTao Box 启动中，请等待约 30 秒...
