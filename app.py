"""
校园水质生态监测与巡检管护管理系统
2024网络工程 WEB网络编程期末项目 | wd小组
wd（数据库） wzl（前端） lyz（后端）
运行：pip install -r requirements.txt && python init_db.py && python app.py
数据库：MySQL 5.5 / 8（库 campus_water），配置见 config.py
访问：http://127.0.0.1:5000  测试账号 admin/admin123
"""
import csv, hashlib, io, random, secrets, time
import pymysql
import pymysql.cursors
import config
from datetime import date, timedelta, datetime
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, Response
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

ROLE_NAMES = {"admin": "系统管理员", "inspector": "巡检员", "reviewer": "审核员"}

class _DB:
    """PyMySQL 连接包装：让 db.execute(sql, args).fetchone()/fetchall() 与 db.commit() 可用。
    PyMySQL 的 Connection 本身没有 execute 方法，必须先取 cursor。"""
    def __init__(self, conn):
        self._conn = conn
        self._cur = None

    def execute(self, sql, args=None):
        self._cur = self._conn.cursor()
        self._cur.execute(sql, args)
        return self._cur

    def commit(self):
        self._conn.commit()

    def close(self):
        try:
            if self._cur is not None:
                self._cur.close()
        finally:
            self._conn.close()


def get_db():
    if "db" not in g:
        conn = pymysql.connect(host=config.DB_HOST, port=config.DB_PORT,
                               user=config.DB_USER, password=config.DB_PASSWORD,
                               database=config.DB_NAME, charset=config.DB_CHARSET,
                               cursorclass=pymysql.cursors.DictCursor, autocommit=False)
        g.db = _DB(conn)
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- 显式加盐密码 ----------
# 不用盐藏在哈希串里看不见的哈希函数，改用标准库 hashlib
# 显式存盐：salt = 16 字节随机盐的 hex（32 位），hash = PBKDF2-HMAC-SHA256 100000 次的 hex。
def hash_password(password):
    """生成新盐并哈希，返回 (salt, hash)。新建账号、改密码时调用，每次重新生成新盐。"""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100000).hex()
    return salt, h

def verify_password(password, salt, stored_hash):
    """用存储的盐重新计算哈希并与 stored_hash 比较。盐缺失/格式错误时返回 False。"""
    if not salt or not stored_hash:
        return False
    try:
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100000).hex()
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(h, stored_hash)

# ---------- 登录验证码 ----------
# 字符集去掉易混淆的 0/O/1/I/l，只剩 32 个字符
CAPTCHA_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def generate_captcha_code(length=None):
    return "".join(random.choice(CAPTCHA_CHARS) for _ in range(length or config.CAPTCHA_LENGTH))

def _captcha_image(code):
    """画 150x50 PNG：白底，每字符随机颜色/位置/轻微旋转，加干扰线和噪点。
    用 ImageFont.load_default()，不依赖系统字体文件。"""
    width, height = 150, 50
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    # 干扰线
    for _ in range(4):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(150, 220), random.randint(150, 220), random.randint(150, 220)), width=1)
    # 噪点
    for _ in range(80):
        draw.point((random.randint(0, width - 1), random.randint(0, height - 1)),
                   fill=(random.randint(150, 230), random.randint(150, 230), random.randint(150, 230)))
    # 字符：逐个画在独立小图上再旋转粘贴，保证轻微旋转不互相覆盖
    slot = width // len(code)
    for i, ch in enumerate(code):
        color = (random.randint(0, 120), random.randint(0, 120), random.randint(0, 120))
        char_img = Image.new("RGBA", (30, 40), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((8, 8), ch, font=font, fill=color + (255,))
        char_img = char_img.rotate(random.randint(-18, 18), resample=Image.BICUBIC, expand=False)
        img.paste(char_img, (i * slot + random.randint(0, 6), random.randint(4, 10)), char_img)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@app.route("/captcha.png", methods=["GET"])
def captcha_png():
    code = generate_captcha_code()
    session["captcha_code"] = code
    session["captcha_expires"] = time.time() + config.CAPTCHA_EXPIRE_SECONDS
    return Response(_captcha_image(code), mimetype="image/png",
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                             "Pragma": "no-cache", "Expires": "0"})

def _check_captcha():
    """校验登录验证码：必填、不区分大小写、一次有效、300 秒过期。
    无论成功失败，用过就清空。返回 (ok, 错误提示或 None)。"""
    code = (request.form.get("captcha") or "").strip().upper()
    stored = session.pop("captcha_code", None)
    expires = session.pop("captcha_expires", None)
    if not code or not stored:
        return False, "验证码错误/已过期，请重新输入"
    if expires is not None and time.time() > float(expires):
        return False, "验证码错误/已过期，请重新输入"
    if code != stored.upper():
        return False, "验证码错误/已过期，请重新输入"
    return True, None

def check_threshold(ph, do, turbidity, ammonia):
    """阈值：pH 6.5-8.5、溶解氧>=5、浑浊度<=10、氨氮<=0.5，任一项不满足即超标"""
    try:
        if not (6.5 <= float(ph) <= 8.5): return "超标"
        if float(do) < 5: return "超标"
        if float(turbidity) > 10: return "超标"
        if float(ammonia) > 0.5: return "超标"
    except (TypeError, ValueError):
        return "超标"
    return "正常"

def log_action(username, action, detail=""):
    db = get_db()
    db.execute("INSERT INTO system_logs(username,action,detail,created_at) VALUES(%s,%s,%s,%s)", (username, action, detail, now()))
    db.commit()

def login_required(f):
    @wraps(f)
    def w(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w

def role_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **kw):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("权限不足：该操作需要 " + "、".join(ROLE_NAMES.get(r, r) for r in roles))
                return redirect(url_for("dashboard"))
            return f(*a, **kw)
        return w
    return deco

@app.context_processor
def inject_user():
    return {"role_names": ROLE_NAMES, "current_user": session.get("username"), "current_role": session.get("role")}

def _date_str(v):
    """PyMySQL 把 DATE 列返回为 datetime.date，SQLite 返回 str；统一转成 YYYY-MM-DD 字符串再比较。"""
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def task_display_status(t):
    """逾期按计划日期自动判定：未完成且计划日期已过 -> 已逾期"""
    if t["status"] != "已完成" and _date_str(t["planned_date"]) < date.today().isoformat():
        return "已逾期"
    return t["status"]

# ---------- 认证 ----------
@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ok, err = _check_captcha()
        if not ok:
            flash(err)
            return render_template("login.html")
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE username=%s", (request.form["username"],)).fetchone()
        if u and verify_password(request.form["password"], u.get("salt"), u["password_hash"]):
            if u["status"] != "active":
                flash("账号已被停用，请联系管理员")
                return render_template("login.html")
            session.update(user_id=u["id"], username=u["username"], role=u["role"], real_name=u["real_name"])
            log_action(u["username"], "登录", "用户登录系统")
            return redirect(url_for("dashboard"))
        flash("用户名或密码错误")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    log_action(session.get("username", ""), "退出登录", "")
    session.clear()
    return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],)).fetchone()
        if not verify_password(request.form["old_password"], u.get("salt"), u["password_hash"]):
            flash("原密码错误")
        elif request.form["new_password"] != request.form["confirm_password"] or not request.form["new_password"]:
            flash("两次新密码不一致或为空")
        else:
            salt, pw_hash = hash_password(request.form["new_password"])
            db.execute("UPDATE users SET salt=%s, password_hash=%s WHERE id=%s", (salt, pw_hash, session["user_id"]))
            db.commit(); log_action(session["username"], "修改密码", "")
            flash("密码修改成功"); return redirect(url_for("dashboard"))
    return render_template("change_password.html")

# ---------- 工作台 ----------
@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    today = date.today()
    meas = db.execute("SELECT COUNT(*) c FROM measurements WHERE result='超标'").fetchone()["c"]
    tasks = db.execute("SELECT t.*, p.name AS point_name FROM inspection_tasks t JOIN monitoring_points p ON p.id=t.point_id ORDER BY t.planned_date").fetchall()
    tasks = [dict(t) for t in tasks]
    for t in tasks: t["display_status"] = task_display_status(t)
    overdue = sum(1 for t in tasks if t["display_status"] == "已逾期")
    done = sum(1 for t in tasks if t["status"] == "已完成")
    total = len(tasks) or 1
    pending_anom = db.execute("SELECT COUNT(*) c FROM anomalies WHERE status='待审核'").fetchone()["c"]
    due_devices = db.execute("SELECT * FROM devices WHERE next_maintenance_date<=%s AND status!='报废'", ((today + timedelta(days=7)).isoformat(),)).fetchall()
    recent = db.execute("SELECT * FROM measurements ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", exceed=meas, tasks=tasks, overdue=overdue,
                           done=done, total=total, rate=round(done/total*100), pending_anom=pending_anom,
                           due_devices=due_devices, recent=recent)

# ---------- 点位 ----------
@app.route("/points")
@login_required
def points():
    db = get_db()
    q = request.args.get("q", "")
    sql = "SELECT * FROM monitoring_points WHERE 1=1"
    args = []
    if q: sql += " AND (name LIKE %s OR code LIKE %s OR location LIKE %s)"; args += [f"%{q}%"]*3
    if request.args.get("type"): sql += " AND type=%s"; args.append(request.args["type"])
    rows = db.execute(sql + " ORDER BY id", args).fetchall()
    return render_template("points.html", points=rows, q=q)

@app.route("/points/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def point_add():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO monitoring_points(code,name,type,location,manager,status,archived,created_at) VALUES(%s,%s,%s,%s,%s,'启用',0,%s)",
                   (request.form["code"], request.form["name"], request.form["type"], request.form["location"], request.form["manager"], now()))
        db.commit(); log_action(session["username"], "新增点位", request.form["name"])
        return redirect(url_for("points"))
    return render_template("point_form.html", point=None)

@app.route("/points/<int:pid>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def point_edit(pid):
    db = get_db()
    p = db.execute("SELECT * FROM monitoring_points WHERE id=%s", (pid,)).fetchone()
    if request.method == "POST":
        db.execute("UPDATE monitoring_points SET code=%s,name=%s,type=%s,location=%s,manager=%s,status=%s WHERE id=%s",
                   (request.form["code"], request.form["name"], request.form["type"], request.form["location"], request.form["manager"], request.form["status"], pid))
        db.commit(); log_action(session["username"], "修改点位", request.form["name"])
        return redirect(url_for("points"))
    return render_template("point_form.html", point=p)

@app.route("/points/<int:pid>/archive", methods=["POST"])
@login_required
@role_required("admin")
def point_archive(pid):
    db = get_db()
    db.execute("UPDATE monitoring_points SET archived=1,status='停用' WHERE id=%s", (pid,)); db.commit()
    log_action(session["username"], "归档点位", f"点位ID {pid}")
    return redirect(url_for("points"))

@app.route("/points/<int:pid>/delete", methods=["POST"])
@login_required
@role_required("admin")
def point_delete(pid):
    db = get_db()
    db.execute("DELETE FROM monitoring_points WHERE id=%s", (pid,)); db.commit()
    log_action(session["username"], "删除点位", f"点位ID {pid}")
    return redirect(url_for("points"))

# ---------- 监测数据 ----------
@app.route("/measurements")
@login_required
def measurements():
    db = get_db()
    sql = "SELECT m.*, p.name AS point_name FROM measurements m JOIN monitoring_points p ON p.id=m.point_id WHERE 1=1"
    args = []
    if request.args.get("point_id"): sql += " AND m.point_id=%s"; args.append(request.args["point_id"])
    if request.args.get("start"): sql += " AND m.measure_date>=%s"; args.append(request.args["start"])
    if request.args.get("end"): sql += " AND m.measure_date<=%s"; args.append(request.args["end"])
    if request.args.get("result"): sql += " AND m.result=%s"; args.append(request.args["result"])
    rows = db.execute(sql + " ORDER BY m.measure_date DESC, m.id DESC", args).fetchall()
    pts = db.execute("SELECT * FROM monitoring_points WHERE status='启用'").fetchall()
    return render_template("measurements.html", rows=rows, points=pts, args=request.args)

@app.route("/measurements/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "inspector")
def measurement_add():
    db = get_db()
    pts = db.execute("SELECT * FROM monitoring_points WHERE status='启用'").fetchall()
    if request.method == "POST":
        r = check_threshold(request.form["ph"], request.form["dissolved_oxygen"], request.form["turbidity"], request.form["ammonia"])
        db.execute("INSERT INTO measurements(point_id,measure_date,temperature,ph,dissolved_oxygen,turbidity,ammonia,recorder,result,remark,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                   (request.form["point_id"], request.form["measure_date"], request.form.get("temperature") or None,
                    request.form["ph"], request.form["dissolved_oxygen"], request.form["turbidity"], request.form["ammonia"],
                    session["username"], r, request.form.get("remark", ""), now()))
        db.commit(); log_action(session["username"], "登记监测数据", f"判定结果：{r}")
        flash(f"登记成功，判定结果：{r}")
        return redirect(url_for("measurements"))
    return render_template("measurement_form.html", points=pts, today=date.today().isoformat())

@app.route("/measurements/<int:mid>/to_anomaly", methods=["POST"])
@login_required
@role_required("admin", "inspector")
def measurement_to_anomaly(mid):
    db = get_db()
    m = db.execute("SELECT m.*, p.name AS point_name FROM measurements m JOIN monitoring_points p ON p.id=m.point_id WHERE m.id=%s", (mid,)).fetchone()
    if m:
        db.execute("INSERT INTO anomalies(point_id,title,type,description,status,reporter,reviewer,review_comment,created_at,updated_at) VALUES(%s,%s,%s,%s, '待审核', %s, '', '', %s, %s)",
                   (m["point_id"], f"{m['point_name']}水质超标（{m['measure_date']}）", "水质超标",
                    f"pH {m['ph']}，溶解氧 {m['dissolved_oxygen']}mg/L，浑浊度 {m['turbidity']}NTU，氨氮 {m['ammonia']}mg/L", session["username"], now(), now()))
        db.commit(); log_action(session["username"], "超标转异常", f"监测ID {mid}")
    return redirect(url_for("anomalies"))

@app.route("/measurements/export")
@login_required
def measurements_export():
    db = get_db()
    rows = db.execute("SELECT m.*, p.name AS point_name FROM measurements m JOIN monitoring_points p ON p.id=m.point_id ORDER BY m.measure_date DESC").fetchall()
    return csv_response("measurements.csv", ["日期", "点位", "水温", "pH", "溶解氧", "浑浊度", "氨氮", "结果", "登记人"],
                        [[r["measure_date"], r["point_name"], r["temperature"], r["ph"], r["dissolved_oxygen"], r["turbidity"], r["ammonia"], r["result"], r["recorder"]] for r in rows])

def csv_response(filename, header, rows):
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(header); w.writerows(rows)
    data = "\ufeff" + buf.getvalue()  # BOM，Excel 直接打开不乱码
    return Response(data, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})

# ---------- 巡检任务 ----------
@app.route("/tasks")
@login_required
def tasks():
    db = get_db()
    rows = [dict(t) for t in db.execute("SELECT t.*, p.name AS point_name FROM inspection_tasks t JOIN monitoring_points p ON p.id=t.point_id ORDER BY t.planned_date").fetchall()]
    for t in rows: t["display_status"] = task_display_status(t)
    return render_template("tasks.html", tasks=rows)

@app.route("/tasks/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def task_add():
    db = get_db(); pts = db.execute("SELECT * FROM monitoring_points WHERE status='启用'").fetchall()
    if request.method == "POST":
        db.execute("INSERT INTO inspection_tasks(point_id,title,cycle,assignee,planned_date,status,result,inspect_time,remark,created_at) VALUES(%s,%s,%s,%s,%s,'待巡检','','','',%s)",
                   (request.form["point_id"], request.form["title"], request.form["cycle"], request.form["assignee"], request.form["planned_date"], now()))
        db.commit(); log_action(session["username"], "派发巡检任务", request.form["title"])
        return redirect(url_for("tasks"))
    return render_template("task_form.html", points=pts)

@app.route("/tasks/<int:tid>/start", methods=["POST"])
@login_required
def task_start(tid):
    db = get_db(); db.execute("UPDATE inspection_tasks SET status='巡检中' WHERE id=%s", (tid,)); db.commit()
    log_action(session["username"], "领取巡检任务", f"任务ID {tid}"); return redirect(url_for("tasks"))

@app.route("/tasks/<int:tid>/finish", methods=["GET", "POST"])
@login_required
def task_finish(tid):
    db = get_db()
    t = db.execute("SELECT * FROM inspection_tasks WHERE id=%s", (tid,)).fetchone()
    if request.method == "POST":
        db.execute("UPDATE inspection_tasks SET status='已完成',result=%s,inspect_time=%s WHERE id=%s",
                   (request.form["result"], request.form.get("inspect_time") or now(), tid))
        db.commit(); log_action(session["username"], "完成巡检任务", f"任务ID {tid}")
        return redirect(url_for("tasks"))
    return render_template("task_finish.html", task=t)

# ---------- 异常审批 ----------
@app.route("/anomalies")
@login_required
def anomalies():
    db = get_db()
    sql = "SELECT a.*, p.name AS point_name FROM anomalies a JOIN monitoring_points p ON p.id=a.point_id WHERE 1=1"
    args = []
    if request.args.get("status"): sql += " AND a.status=%s"; args.append(request.args["status"])
    rows = db.execute(sql + " ORDER BY a.id DESC", args).fetchall()
    return render_template("anomalies.html", rows=rows)

@app.route("/anomalies/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "inspector")
def anomaly_add():
    db = get_db(); pts = db.execute("SELECT * FROM monitoring_points").fetchall()
    if request.method == "POST":
        db.execute("INSERT INTO anomalies(point_id,title,type,description,status,reporter,reviewer,review_comment,created_at,updated_at) VALUES(%s,%s,%s,%s, '待审核', %s, '', '', %s, %s)",
                   (request.form["point_id"], request.form["title"], request.form["type"], request.form["description"], session["username"], now(), now()))
        db.commit(); log_action(session["username"], "登记异常", request.form["title"])
        return redirect(url_for("anomalies"))
    return render_template("anomaly_form.html", points=pts)

@app.route("/anomalies/<int:aid>/review", methods=["POST"])
@login_required
@role_required("reviewer", "admin")
def anomaly_review(aid):
    db = get_db()
    action = request.form["action"]; comment = request.form.get("comment", "")
    new = "待整改" if action == "approve" else "已驳回"
    db.execute("UPDATE anomalies SET status=%s, reviewer=%s, review_comment=%s, updated_at=%s WHERE id=%s",
               (new, session["username"], comment, now(), aid))
    db.commit(); log_action(session["username"], "审核异常", f"异常ID {aid} -> {new}")
    return redirect(url_for("anomalies"))

@app.route("/anomalies/<int:aid>/status", methods=["POST"])
@login_required
def anomaly_status(aid):
    db = get_db()
    new = request.form["status"]
    if new not in ("待复查", "已归档"):
        flash("非法状态流转"); return redirect(url_for("anomalies"))
    db.execute("UPDATE anomalies SET status=%s, updated_at=%s WHERE id=%s", (new, now(), aid)); db.commit()
    log_action(session["username"], "异常状态变更", f"异常ID {aid} -> {new}")
    return redirect(url_for("anomalies"))

# ---------- 设备运维 ----------
@app.route("/devices")
@login_required
def devices():
    db = get_db()
    rows = db.execute("SELECT d.*, p.name AS point_name FROM devices d LEFT JOIN monitoring_points p ON p.id=d.point_id ORDER BY d.id").fetchall()
    today = date.today(); due = []
    for r in rows:
        nxt = r["next_maintenance_date"] if isinstance(r["next_maintenance_date"], date) else date.fromisoformat(r["next_maintenance_date"])
        if nxt <= today + timedelta(days=7): due.append(r["name"])
    return render_template("devices.html", devices=rows, due=due, today=today.isoformat())

@app.route("/devices/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def device_add():
    db = get_db(); pts = db.execute("SELECT * FROM monitoring_points").fetchall()
    if request.method == "POST":
        db.execute("INSERT INTO devices(code,name,type,point_id,install_date,next_maintenance_date,status,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                   (request.form["code"], request.form["name"], request.form["type"], request.form.get("point_id") or None,
                    request.form["install_date"], request.form["next_maintenance_date"], request.form["status"], now()))
        db.commit(); log_action(session["username"], "登记设备", request.form["name"])
        return redirect(url_for("devices"))
    return render_template("device_form.html", points=pts, today=date.today().isoformat())

@app.route("/devices/<int:did>/maintain", methods=["GET", "POST"])
@login_required
def device_maintain(did):
    db = get_db()
    d = db.execute("SELECT * FROM devices WHERE id=%s", (did,)).fetchone()
    if request.method == "POST":
        db.execute("INSERT INTO maintenance_logs(device_id,type,content,maintainer,maintain_date,created_at) VALUES(%s,%s,%s,%s,%s,%s)",
                   (did, request.form["type"], request.form["content"], session["username"], request.form["maintain_date"], now()))
        if request.form.get("next_maintenance_date"):
            db.execute("UPDATE devices SET next_maintenance_date=%s, status=%s WHERE id=%s",
                       (request.form["next_maintenance_date"], request.form.get("device_status", "正常"), did))
        db.commit(); log_action(session["username"], "设备维保", f"设备 {d['name']}")
        return redirect(url_for("devices"))
    logs_ = db.execute("SELECT * FROM maintenance_logs WHERE device_id=%s ORDER BY maintain_date DESC", (did,)).fetchall()
    return render_template("device_maintain.html", device=d, logs=logs_, today=date.today().isoformat())

# ---------- 统计 ----------
@app.route("/stats")
@login_required
def stats():
    db = get_db()
    point_stats = db.execute("SELECT * FROM v_point_stats").fetchall()
    total_m = db.execute("SELECT COUNT(*) c FROM measurements").fetchone()["c"] or 1
    exceed = db.execute("SELECT COUNT(*) c FROM measurements WHERE result='超标'").fetchone()["c"]
    tasks_total = db.execute("SELECT COUNT(*) c FROM inspection_tasks").fetchone()["c"] or 1
    tasks_done = db.execute("SELECT COUNT(*) c FROM inspection_tasks WHERE status='已完成'").fetchone()["c"]
    faults = db.execute("SELECT COUNT(*) c FROM maintenance_logs WHERE type IN ('维修','故障处理')").fetchone()["c"]
    anoms = db.execute("SELECT status, COUNT(*) c FROM anomalies GROUP BY status").fetchall()
    return render_template("stats.html", point_stats=point_stats, total_m=total_m, exceed=exceed,
                           exceed_rate=round(exceed/total_m*100, 1), tasks_total=tasks_total, tasks_done=tasks_done,
                           task_rate=round(tasks_done/tasks_total*100, 1), faults=faults, anoms=anoms)

@app.route("/stats/export")
@login_required
def stats_export():
    db = get_db()
    rows = db.execute("SELECT * FROM v_point_stats").fetchall()
    return csv_response("stats.csv", ["点位", "监测总数", "pH均值", "溶解氧均值", "浑浊度均值", "氨氮均值", "超标次数"],
                        [[r["point_name"], r["total"], r["avg_ph"], r["avg_do"], r["avg_turbidity"], r["avg_ammonia"], r["exceed_count"]] for r in rows])

# ---------- 档案 ----------
@app.route("/archives")
@login_required
def archives():
    db = get_db()
    rows = db.execute("""SELECT YEAR(measure_date) AS year, p.name AS point_name,
        COUNT(*) AS m_count, SUM(CASE WHEN result='超标' THEN 1 ELSE 0 END) AS exceed_count
        FROM measurements m JOIN monitoring_points p ON p.id=m.point_id GROUP BY year, point_name ORDER BY year DESC""").fetchall()
    task_rows = db.execute("SELECT YEAR(planned_date) AS year, COUNT(*) c, SUM(CASE WHEN status='已完成' THEN 1 ELSE 0 END) done FROM inspection_tasks GROUP BY year").fetchall()
    return render_template("archives.html", rows=rows, task_rows=task_rows)

@app.route("/archives/export")
@login_required
def archives_export():
    db = get_db()
    rows = db.execute("""SELECT YEAR(measure_date) AS year, p.name AS point_name, COUNT(*) c,
        SUM(CASE WHEN result='超标' THEN 1 ELSE 0 END) e FROM measurements m JOIN monitoring_points p ON p.id=m.point_id GROUP BY year, point_name""").fetchall()
    return csv_response("archives.csv", ["年度", "点位", "监测记录数", "超标次数"],
                        [[r["year"], r["point_name"], r["c"], r["e"]] for r in rows])

# ---------- 用户与日志 ----------
@app.route("/users")
@login_required
@role_required("admin")
def users():
    db = get_db()
    return render_template("users.html", users=db.execute("SELECT * FROM users ORDER BY id").fetchall())

@app.route("/users/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def user_add():
    if request.method == "POST":
        db = get_db()
        try:
            salt, pw_hash = hash_password(request.form["password"])
            db.execute("INSERT INTO users(username,salt,password_hash,real_name,role,status,created_at) VALUES(%s,%s,%s,%s,%s, 'active', %s)",
                       (request.form["username"], salt, pw_hash, request.form["real_name"], request.form["role"], now()))
            db.commit(); log_action(session["username"], "创建账号", request.form["username"])
        except pymysql.err.IntegrityError:
            flash("用户名已存在")
            return render_template("user_form.html")
        return redirect(url_for("users"))
    return render_template("user_form.html")

@app.route("/users/<int:uid>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def user_toggle(uid):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=%s", (uid,)).fetchone()
    new = "disabled" if u["status"] == "active" else "active"
    db.execute("UPDATE users SET status=%s WHERE id=%s", (new, uid)); db.commit()
    log_action(session["username"], "启用/停用账号", f"{u['username']} -> {new}")
    return redirect(url_for("users"))

@app.route("/logs")
@login_required
@role_required("admin")
def logs():
    db = get_db()
    rows = db.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 200").fetchall()
    return render_template("logs.html", logs=rows)

if __name__ == "__main__":
    print("校园水质生态监测与巡检管护管理系统已启动：http://127.0.0.1:5000")
    print("测试账号：admin / admin123（系统管理员） inspector1 / 123456（巡检员） reviewer / 123456（审核员）")
    app.run(host="127.0.0.1", port=5000, debug=False)
