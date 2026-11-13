@echo off
chcp 65001 >nul
cd /d %~dp0
echo 正在安装依赖...
pip install -r requirements.txt
echo 正在初始化数据库（首次运行建库建表并写入演示数据，已有数据不会重复写入）...
python init_db.py
echo 启动系统，打开浏览器访问 http://127.0.0.1:5000
python app.py
pause
