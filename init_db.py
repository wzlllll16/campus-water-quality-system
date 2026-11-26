# -*- coding: utf-8 -*-
"""
一键初始化数据库：建库 -> 建表 -> 写演示数据 -> 建视图/触发器
用法（Windows）：python init_db.py
要求：MySQL 5.5 或 8 已启动，config.py 里的账号密码正确。
可重复运行：建表用 IF NOT EXISTS，演示数据只在 users 为空时写入。
旧库迁移：若 users 表还没有 salt 列（旧版建的库），自动 ALTER TABLE 加列，
并把旧的 scrypt: 开头哈希按演示账号已知密码用新加盐算法重写。
注意：已跑过旧版的用户，建议先在 MySQL 里执行 DROP DATABASE campus_water;
再跑 python init_db.py，得到干净的新库。
"""
import hashlib
import os
import secrets
import pymysql
import config

# 旧版演示账号的已知密码，仅用于旧库迁移时重写哈希（与 README 测试账号表一致）
DEMO_PASSWORDS = {"admin": "admin123", "inspector1": "123456", "inspector2": "123456",
                  "reviewer": "123456", "admin2": "123456"}


def _hash_password(password):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100000).hex()
    return salt, h


def migrate_users_table(conn):
    """旧库迁移：补 salt 列，并重写旧 scrypt 哈希（或盐丢失的行）为新加盐哈希。"""
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM users LIKE 'salt'")
        if cur.fetchone() is None:
            cur.execute("ALTER TABLE users ADD COLUMN salt CHAR(32) NOT NULL AFTER password_hash")
            cur.execute("ALTER TABLE users MODIFY password_hash VARCHAR(128) NOT NULL")
            print("旧库迁移：users 表已补 salt 列")
        cur.execute("SELECT username, password_hash FROM users WHERE password_hash LIKE 'scrypt:%' OR salt=''")
        old = cur.fetchall()
        for username, _old_hash in old:
            pw = DEMO_PASSWORDS.get(username)
            if pw is None:
                print(f"旧库迁移：跳过非演示账号 {username}（旧哈希无法自动转换，请管理员重置其密码）")
                continue
            salt, pw_hash = _hash_password(pw)
            cur.execute("UPDATE users SET salt=%s, password_hash=%s WHERE username=%s",
                        (salt, pw_hash, username))
            print(f"旧库迁移：账号 {username} 的密码已按新加盐算法重写")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def connect_no_db():
    return pymysql.connect(host=config.DB_HOST, port=config.DB_PORT,
                           user=config.DB_USER, password=config.DB_PASSWORD,
                           charset=config.DB_CHARSET, autocommit=True)


def connect_db():
    return pymysql.connect(host=config.DB_HOST, port=config.DB_PORT,
                           user=config.DB_USER, password=config.DB_PASSWORD,
                           database=config.DB_NAME, charset=config.DB_CHARSET,
                           autocommit=True)


def run_sql_file(conn, path):
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    # 按分号切分执行；本项目 SQL 文件中没有含分号的字符串/触发器体（触发器为单条语句），可安全切分
    with conn.cursor() as cur:
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)


def main():
    print(f"连接 MySQL：{config.DB_HOST}:{config.DB_PORT} 用户 {config.DB_USER}")
    conn = connect_no_db()
    run_sql_file(conn, os.path.join(BASE_DIR, "database", "schema.sql"))
    conn.close()
    print(f"数据库 {config.DB_NAME} 与 9 张表已创建")
    conn = connect_db()
    migrate_users_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
    if user_count == 0:
        run_sql_file(conn, os.path.join(BASE_DIR, "database", "seed.sql"))
        print("演示数据已写入：5账号 / 6点位 / 10监测 / 6任务 / 5异常 / 6设备 / 4维保")
    else:
        print(f"users 已有 {user_count} 条记录，跳过演示数据写入")
    run_sql_file(conn, os.path.join(BASE_DIR, "database", "views.sql"))
    conn.close()
    print("视图与触发器已创建：v_point_stats / v_task_completion / v_anomaly_stats / trg_measurement_exceed")
    print("初始化完成，运行 python app.py 后访问 http://127.0.0.1:5000")


if __name__ == "__main__":
    main()
