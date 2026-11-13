# -*- coding: utf-8 -*-
"""
数据库与应用配置 — 只改这里
校园水质生态监测与巡检管护管理系统 | wd小组
"""
# MySQL 5.5 / 8 数据库连接（本机）
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
# 改成你安装 MySQL 时设置的 root 密码（phpStudy 里就是你登录 MySQL 用的那个密码）；若 root 无密码，改为 ""
DB_PASSWORD = "123456"
DB_NAME = "campus_water"
DB_CHARSET = "utf8mb4"

# Flask 会话密钥（演示用，正式使用请改成随机字符串）
SECRET_KEY = "campus-water-quality-2024"
