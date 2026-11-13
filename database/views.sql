-- 统计视图与触发器示例（MySQL 5.5 / 8 / MariaDB 兼容）
USE campus_water;

-- 视图1：点位指标统计 — 各点位监测总数、各指标均值、超标次数与超标率
CREATE OR REPLACE VIEW v_point_stats AS
SELECT p.id AS point_id, p.name AS point_name, COUNT(m.id) AS total,
  ROUND(AVG(m.ph), 2) AS avg_ph,
  ROUND(AVG(m.dissolved_oxygen), 2) AS avg_do,
  ROUND(AVG(m.turbidity), 2) AS avg_turbidity,
  ROUND(AVG(m.ammonia), 2) AS avg_ammonia,
  SUM(CASE WHEN m.result = '超标' THEN 1 ELSE 0 END) AS exceed_count,
  ROUND(100.0 * SUM(CASE WHEN m.result = '超标' THEN 1 ELSE 0 END) / NULLIF(COUNT(m.id), 0), 1) AS exceed_rate
FROM monitoring_points p
LEFT JOIN measurements m ON m.point_id = p.id
GROUP BY p.id, p.name;

-- 视图2：巡检完成率 — 按责任人统计任务总数、已完成数、完成率
CREATE OR REPLACE VIEW v_task_completion AS
SELECT assignee, COUNT(*) AS total,
  SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END) AS done_count,
  ROUND(100.0 * SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END) / COUNT(*), 1) AS completion_rate
FROM inspection_tasks
GROUP BY assignee;

-- 视图3：异常处理统计 — 按状态统计异常数、平均处理时长（天）
CREATE OR REPLACE VIEW v_anomaly_stats AS
SELECT status, COUNT(*) AS total,
  ROUND(AVG(DATEDIFF(updated_at, created_at)), 1) AS avg_handle_days
FROM anomalies
GROUP BY status;

-- 触发器示例：登记监测数据后，若判定为超标，自动在系统日志写一条超标提醒
-- 用途：超标情况发现不及时的问题 — 数据一入库就留痕，工作台可据此提醒；
-- 触发器本身不自动生成异常记录，是否转异常仍由巡检员在页面点“一键转异常”决定。
-- 写法为单条条件 INSERT（SELECT ... WHERE ...），无需 DELIMITER，可直接由 init_db.py 执行。
DROP TRIGGER IF EXISTS trg_measurement_exceed;
CREATE TRIGGER trg_measurement_exceed
AFTER INSERT ON measurements
FOR EACH ROW
  INSERT INTO system_logs (username, action, detail, created_at)
  SELECT NEW.recorder, '超标自动提醒',
         CONCAT('点位ID ', NEW.point_id, ' 在 ', NEW.measure_date, ' 的监测超标：pH ', NEW.ph, '，溶解氧 ', NEW.dissolved_oxygen, '，浑浊度 ', NEW.turbidity, '，氨氮 ', NEW.ammonia),
         NOW()
  FROM DUAL WHERE NEW.result = '超标';
