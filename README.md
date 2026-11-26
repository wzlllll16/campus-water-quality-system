# 校园水质生态监测与巡检管护管理系统

2024 网络工程专业 WEB 网络编程期末项目 · wd小组
B/S 架构，Python 3 + Flask + **MySQL 5.5 / 8**（PyMySQL 连接），无 npm、无云服务，在自己电脑上运行。

> 兼容说明：本版已按 MySQL 5.5 改过，`DATETIME DEFAULT CURRENT_TIMESTAMP`（MySQL 5.6.5 才支持）已全部改成 `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`；`anomalies.updated_at` 用固定默认值，程序和演示数据都会显式写入时间，不依赖数据库默认值。MySQL 8 上同样能跑。

## 小组分工

| 成员 | 分工 |
|---|---|
| wd | 数据库设计与维护（E-R 图、表结构、视图/触发器），统计分析与档案查询的 SQL 实现，测试数据准备，报告整理 |
| wzl | 前端开发：全部页面设计与实现（登录页、系统首页工作台、点位台账、数据登记、巡检任务、异常审批、设备维保、统计报表、系统日志页面） |
| lyz | 后端开发：权限控制、点位/监测数据/巡检/异常审批/设备维保/系统日志等接口与业务逻辑，前后端联调、测试 |

## Windows 运行步骤

1. **安装 MySQL**：已有 phpStudy 自带的 MySQL 5.5 也可以直接用（已按 5.5 语法改过），确保 MySQL 服务已启动，记住 root 密码。没有 MySQL 的话，从 https://dev.mysql.com/downloads/mysql/ 下载 MySQL Installer，安装 MySQL Server 8.0，安装时设置 root 密码（例如 `123456`）。安装后可用命令行验证：
   ```bat
   mysql -u root -p
   ```
   能登录并显示版本号（如 `5.5.27` 或 `8.0.x`）就说明服务正常。
2. **安装 Python 3.10+**：从 https://www.python.org/downloads/ 下载，安装时勾选 **Add Python to PATH**。本版 requirements 已升级到 Flask 3.1.2，支持 Python 3.14。
3. 解压本文件夹，打开命令行（Win+R 输入 `cmd`），进入本文件夹，例如：
   ```bat
   cd /d D:\campus-water-quality-local
   ```
4. **改数据库密码**：打开 `config.py`，把 `DB_PASSWORD = "123456"` 改成你安装 MySQL / phpStudy 里登录 MySQL 用的那个 root 密码；如果 root 没有密码，改为 `""`。其他配置一般不用改：`DB_HOST=127.0.0.1`、`DB_PORT=3306`、`DB_USER=root`、`DB_NAME=campus_water`。phpStudy 的 MySQL 默认端口一般也是 3306，如果你改过端口，`DB_PORT` 也要跟着改。
5. 安装依赖（包含登录验证码用的 Pillow）：
   ```bat
   pip install -r requirements.txt
   ```
   若 pip 很慢，可用：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
   依赖：Flask 3.1.2、PyMySQL 1.1.1、Pillow 11.3.0。
6. **初始化数据库**（一键建库、建表、写演示数据、建视图和触发器）：
   ```bat
   python init_db.py
   ```
   成功会显示“初始化完成”。可重复运行，已有演示数据不会重复写入。
   > **旧版升级注意**：已跑过旧版（无 salt 列、无验证码）的用户，先在 MySQL 里执行 `DROP DATABASE campus_water;` 再跑 `python init_db.py`，得到干净的新库。如果不想删库直接跑也可以：`init_db.py` 会自动给 `users` 表补 `salt` 列，并把 5 个演示账号的旧哈希按新加盐算法重写，但其他自己建的账号若还是旧哈希则无法自动转换，需管理员重置密码。
7. 启动：
   ```bat
   python app.py
   ```
   或直接双击 `run.bat`（它会自动依次执行安装依赖、初始化数据库、启动）。
8. 打开浏览器访问 http://127.0.0.1:5000
9. 停止：回到命令行按 `Ctrl+C`。

Mac / Linux：`bash run.sh`，或依次执行 `pip3 install -r requirements.txt`、`python3 init_db.py`、`python3 app.py`。

## 测试账号（初始化时自动写入）

| 用户名 | 密码 | 角色 |
|---|---|---|
| admin | admin123 | 系统管理员 |
| inspector1 | 123456 | 巡检员 |
| inspector2 | 123456 | 巡检员 |
| reviewer | 123456 | 审核员 |
| admin2 | 123456 | 系统管理员 |

不开放自主注册，账号由管理员在“账号管理”里创建，可启用/停用。

## 预置演示数据（初始化时自动写入）

6 个监测点位、10 条监测记录（正常与超标混合）、6 个巡检任务、5 条不同状态的异常记录、6 台设备、4 条维保日志。

## 功能说明（9 项全部实现）

1. **账号权限**：三角色菜单与操作按角色控制，登录、改密码、启用/停用。
2. **点位台账**：编号、类型（湖泊/景观水池/绿化带）、位置、负责人、启用状态，增删改查、归档。
3. **监测数据**：水温、pH、溶解氧、浑浊度、氨氮；阈值 pH 6.5–8.5、溶解氧 ≥5 mg/L、浑浊度 ≤10 NTU、氨氮 ≤0.5 mg/L，自动判定正常/超标并标红；按日期/点位/结果筛选；超标可一键转异常。
4. **巡检任务**：管理员派发，巡检员领取、登记结果与时间；状态 待巡检 → 巡检中 → 已完成，未完成且过了计划日期自动显示“已逾期”。
5. **异常审批**：待审核 →（通过）待整改 → 待复查 → 已归档；（驳回）已驳回，退回补充。
6. **设备运维**：设备登记、故障/维修/维保日志，7 天内到期的维保在工作台和设备页提示。
7. **统计分析**：按点位统计各指标均值、超标次数与超标率，巡检完成率、设备故障次数；导出 CSV（带 BOM，Excel 可直接打开）。
8. **档案管理**：按年度/点位汇总监测与巡检档案，查询与导出 CSV。
9. **系统日志**：记录登录、数据登记、任务变更、审批、数据修改等操作（管理员可见）。

## 数据库说明

- 库名 `campus_water`，字符集 `utf8mb4`。
- 9 张表：`users`、`monitoring_points`、`measurements`、`inspection_tasks`、`anomalies`、`devices`、`maintenance_logs`、`archives`、`system_logs`，含主键、外键、索引、AUTO_INCREMENT，见 `database/schema.sql`。
- 3 个视图：`v_point_stats`（点位指标统计）、`v_task_completion`（巡检完成率）、`v_anomaly_stats`（异常处理统计），见 `database/views.sql`。
- 1 个触发器：`trg_measurement_exceed`，登记监测数据后若判定超标，自动在 `system_logs` 写一条超标提醒；是否转异常仍由巡检员在页面点“一键转异常”决定。
- 演示数据见 `database/seed.sql`，密码为显式加盐 PBKDF2-HMAC-SHA256 哈希（见下节“加盐密码设计”）。

## 项目结构

```
app.py                 # Flask 应用：路由、权限装饰器、阈值判定、日志、统计（PyMySQL，%s 占位符）
config.py              # 数据库与应用配置（只改这里的 DB_PASSWORD）
init_db.py             # 一键初始化：建库 -> 建表 -> 演示数据 -> 视图/触发器
requirements.txt       # Flask + PyMySQL + Pillow（登录验证码）
run.bat / run.sh       # 一键启动脚本
database/
  schema.sql           # 建库、9 张表
  seed.sql             # 演示数据
  views.sql            # 3 个视图 + 1 个触发器
templates/             # Jinja 模板：base、login、dashboard、points、measurements、
                       # tasks、anomalies、devices、stats、archives、users、logs 等
static/style.css       # 全部样式
```

## 加盐密码设计

密码不再用隐藏盐的哈希函数，改用标准库 `hashlib` 显式加盐，函数在 `app.py`：

- `hash_password(password) -> (salt, hash)`：`salt = secrets.token_hex(16)`（16 字节随机盐，存为 32 位 hex），`hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000).hex()`（64 位 hex）。
- `verify_password(password, salt, stored_hash)`：用存储的盐按同样算法重算一次哈希，再用 `secrets.compare_digest` 比较；盐缺失或格式错误返回 False。
- `users` 表：`salt CHAR(32) NOT NULL`，`password_hash VARCHAR(128) NOT NULL`（存 64 位 hex 哈希）。

为什么每个用户单独随机盐：

- **同一密码哈希不同**：5 个演示账号里 inspector1、inspector2、reviewer、admin2 密码都是 123456，但盐各不相同，哈希也各不相同，数据库泄露后看不出哪些账号用了相同密码。
- **防彩虹表**：攻击者不能用预先算好的常用密码哈希表直接比对，必须针对每个盐单独算，100000 次 PBKDF2 迭代又让每次猜测都很慢。
- **改密码换新盐**：登录、改密码、管理员新建账号三处都用这两个函数，新建/改密码时重新生成新盐；旧密码的盐和哈希作废。

## 验证码设计

登录页（仅登录页，其他页面不加）有图片验证码，`GET /captcha.png`：

- **生成**：5 位字符（`config.py` 的 `CAPTCHA_LENGTH=5`），字符集去掉易混淆的 0/O/1/I/l，只用 `23456789ABCDEFGHJKLMNPQRSTUVWXYZ`。
- **图片**：Pillow 画 150×50 PNG，白底，每字符随机颜色/位置/轻微旋转（±18°），加 4 条干扰线和 80 个噪点；用 `ImageFont.load_default()`，不依赖系统字体文件；返回 `image/png` 并加 `no-cache` 头。
- **存储**：验证码明文存在 Flask session（`session['captcha_code']`），过期时间 `session['captcha_expires']` = 当前时间 + 300 秒（`CAPTCHA_EXPIRE_SECONDS=300`），只存在服务端，不写数据库。
- **校验**：登录先校验验证码再校验用户名密码；验证码必填、不区分大小写；**一次有效**——无论成功失败，用过就清空 session 里的验证码，同一码第二次登录必然失败；超过 300 秒算过期，提示“验证码错误/已过期，请重新输入”并重新生成。
- **刷新**：点击验证码图片或“看不清？换一张”重新获取，请求带时间戳参数防缓存。

## 重置数据

在 MySQL 里删除数据库后重新初始化：
```sql
DROP DATABASE campus_water;
```
再运行 `python init_db.py` 即可重新建库并写入演示数据。

## 常见问题

- `ModuleNotFoundError: No module named 'pymysql'`：依赖没装到 VSCode 用的那个 Python 上。VSCode 只负责运行，不会自动装库。必须用**同一个 Python**装，在 VSCode 终端里运行（把下面路径换成你截图里那个 python.exe）：
  ```powershell
  & 'C:\Users\wzl\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m pip install -r requirements.txt
  ```
  装完验证：`...\python.exe -c "import pymysql, flask; print('ok')"` 显示 ok 再跑 `init_db.py`。
- `Access denied for user 'root'@'localhost'`：`config.py` 里的 `DB_PASSWORD` 与 MySQL root 密码不一致，改成安装时设置的密码。
- `Can't connect to MySQL server on '127.0.0.1:3306'`：MySQL 服务没启动，phpStudy 里启动 MySQL，或在 Windows 服务里启动 MySQL。
- `Invalid default value for 'created_at'`：这是旧版在 MySQL 5.5 上的报错，本版已修复；如果你还看到它，说明用的还是旧 zip，重新下载本版再试。
- `Unknown database 'campus_water'`：先运行 `python init_db.py` 再运行 `python app.py`。
- 导出为 CSV 文件（带 BOM），用 Excel 打开不乱码；不是原生 .xlsx。
- 本系统仅供校内工作人员演示使用，不要把测试账号和密码用于真实生产环境。
