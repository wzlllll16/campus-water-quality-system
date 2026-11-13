-- 演示数据：5账号 / 6点位 / 10监测 / 6任务 / 5异常 / 6设备 / 4维保
-- 密码哈希与原来一致（werkzeug scrypt）：admin123、123456
-- 账号：admin/admin123、inspector1/123456、inspector2/123456、reviewer/123456、admin2/123456
-- 仅在 users 为空时由 init_db.py 执行，避免重复写入
USE campus_water;

INSERT INTO users (username, password_hash, real_name, role, status) VALUES
('admin', 'scrypt:32768:8:1$LQsNrnjP6LgQO7Tm$db7060329e6219023f98de077b2350c92c5ad210c236206d82125239b5ce3a4889f1c9a226ef5712a7fda254b415a2eeb32889aa4a72484f0656d46b9e954fc6', 'wd', 'admin', 'active'),
('inspector1', 'scrypt:32768:8:1$L55QPxovaODwPzie$bfbbca65d22887f7199a287cb84f72d82c9288fa4ce58deae0205e971cbf239a3977b48d00e86b73d3b486128ccd1e942c746496a24c1196995dd7c1b0d4d92c', 'wzl', 'inspector', 'active'),
('inspector2', 'scrypt:32768:8:1$L55QPxovaODwPzie$bfbbca65d22887f7199a287cb84f72d82c9288fa4ce58deae0205e971cbf239a3977b48d00e86b73d3b486128ccd1e942c746496a24c1196995dd7c1b0d4d92c', 'lyz', 'inspector', 'active'),
('reviewer', 'scrypt:32768:8:1$L55QPxovaODwPzie$bfbbca65d22887f7199a287cb84f72d82c9288fa4ce58deae0205e971cbf239a3977b48d00e86b73d3b486128ccd1e942c746496a24c1196995dd7c1b0d4d92c', '审核员', 'reviewer', 'active'),
('admin2', 'scrypt:32768:8:1$L55QPxovaODwPzie$bfbbca65d22887f7199a287cb84f72d82c9288fa4ce58deae0205e971cbf239a3977b48d00e86b73d3b486128ccd1e942c746496a24c1196995dd7c1b0d4d92c', '管理员', 'admin', 'active');

INSERT INTO monitoring_points (code, name, type, location, manager, status) VALUES
('JD001', '明德湖', '湖泊', '校园东区明德湖', 'wzl', '启用'),
('JD002', '景观水池·图书馆前', '景观水池', '图书馆前广场', 'lyz', '启用'),
('JD003', '绿化带·南苑', '绿化带', '南苑宿舍区绿化带', 'wzl', '启用'),
('JD004', '荷花池', '景观水池', '校园西区荷花池', 'lyz', '启用'),
('JD005', '人工湖·北区', '湖泊', '校园北区人工湖', 'wzl', '启用'),
('JD006', '绿化带·运动场东', '绿化带', '运动场东侧绿化带', 'lyz', '启用');

INSERT INTO measurements (point_id, measure_date, temperature, ph, dissolved_oxygen, turbidity, ammonia, recorder, result, remark) VALUES
(1, '2026-11-10', 18.5, 7.20, 6.80, 4.50, 0.22, 'wzl', '正常', ''),
(1, '2026-11-11', 18.0, 7.50, 6.20, 5.00, 0.30, 'wzl', '正常', ''),
(2, '2026-11-10', 19.0, 7.00, 5.80, 6.00, 0.18, 'lyz', '正常', ''),
(2, '2026-11-11', 20.0, 8.90, 4.20, 12.50, 0.80, 'lyz', '超标', 'pH偏高、浑浊度超标'),
(3, '2026-11-10', 17.5, 7.10, 6.50, 3.80, 0.15, 'wzl', '正常', ''),
(4, '2026-11-11', 19.5, 6.10, 4.80, 9.00, 0.55, 'lyz', '超标', 'pH偏低、氨氮超标'),
(5, '2026-11-10', 18.2, 7.30, 7.00, 4.00, 0.20, 'wzl', '正常', ''),
(5, '2026-11-12', 18.8, 7.40, 6.90, 4.20, 0.25, 'wzl', '正常', ''),
(6, '2026-11-11', 17.0, 7.00, 6.00, 5.50, 0.28, 'lyz', '正常', ''),
(3, '2026-11-12', 17.8, 9.10, 3.90, 15.00, 0.90, 'wzl', '超标', '多项超标');

INSERT INTO inspection_tasks (point_id, title, cycle, assignee, planned_date, status, result, inspect_time) VALUES
(1, '明德湖日常巡检', '每周', 'wzl', '2026-11-12', '已完成', '水面清洁，无异常', '2026-11-12'),
(2, '图书馆水池巡检', '每周', 'lyz', '2026-11-13', '巡检中', '', NULL),
(3, '南苑绿化带巡检', '每月', 'wzl', '2026-11-14', '待巡检', '', NULL),
(4, '荷花池水质复查', '每周', 'lyz', '2026-11-10', '已完成', '已复查，氨氮仍偏高', '2026-11-10'),
(5, '北区人工湖巡检', '每周', 'wzl', '2026-11-09', '待巡检', '', NULL),
(6, '运动场绿化带巡检', '每月', 'lyz', '2026-11-15', '待巡检', '', NULL);

INSERT INTO anomalies (point_id, title, type, description, status, reporter, created_at, updated_at) VALUES
(2, '图书馆水池pH超标', '水质超标', 'pH 8.9，浑浊度12.5NTU，氨氮0.8mg/L', '待审核', 'lyz', NOW(), NOW()),
(4, '荷花池氨氮超标', '水质超标', '氨氮0.55mg/L，溶解氧4.8mg/L', '待整改', 'lyz', NOW(), NOW()),
(3, '南苑绿化带喷灌设备漏水', '设施损坏', '喷灌管道接口漏水', '待复查', 'wzl', NOW(), NOW()),
(1, '明德湖增氧机异响', '设施损坏', '增氧机运行异响，已停机检查', '已归档', 'wzl', NOW(), NOW()),
(2, '图书馆水池水泵故障', '设施损坏', '水泵无法启动', '已驳回', 'lyz', NOW(), NOW());

INSERT INTO devices (code, name, type, point_id, install_date, next_maintenance_date, status) VALUES
('SB001', '水质传感器A', '水质传感器', 1, '2025-09-01', DATE_ADD(CURDATE(), INTERVAL 5 DAY), '正常'),
('SB002', '水泵·图书馆水池', '水泵', 2, '2025-09-01', DATE_ADD(CURDATE(), INTERVAL 30 DAY), '正常'),
('SB003', '增氧机·明德湖', '增氧机', 1, '2025-09-01', DATE_ADD(CURDATE(), INTERVAL 3 DAY), '正常'),
('SB004', '水质传感器B', '水质传感器', 5, '2025-10-01', DATE_ADD(CURDATE(), INTERVAL 60 DAY), '正常'),
('SB005', '水泵·荷花池', '水泵', 4, '2025-10-01', DATE_ADD(CURDATE(), INTERVAL 12 DAY), '正常'),
('SB006', '增氧机·北区人工湖', '增氧机', 5, '2025-10-01', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '故障');

INSERT INTO maintenance_logs (device_id, type, content, maintainer, maintain_date) VALUES
(1, '定期维保', '传感器校准、清洁探头', 'wzl', '2026-11-05'),
(3, '维修', '增氧机异响排查，更换轴承', 'lyz', '2026-11-06'),
(2, '维修', '水泵无法启动，检查电路后恢复', 'lyz', '2026-11-08'),
(6, '故障处理', '增氧机停机，待更换电机', 'wzl', '2026-11-11');

INSERT INTO archives (year, point_id, record_count, exceed_count, summary) VALUES
(2026, 1, 2, 0, '明德湖2026年度监测档案'),
(2026, 2, 2, 1, '图书馆水池2026年度监测档案，含1次超标');
