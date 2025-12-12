@echo off
call .venv\Scripts\activate
echo 虚拟环境已激活
python --version
echo.
echo 可用命令：
echo   python backend/main.py     - 启动后端服务器
echo   cd frontend && npm run dev - 启动前端服务器
echo.
pause