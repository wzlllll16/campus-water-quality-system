-- 演示数据：5账号 / 6点位 / 10监测 / 6任务 / 5异常 / 6设备 / 4维保
-- 密码为显式加盐 PBKDF2-HMAC-SHA256（100000 次）哈希：每账号独立随机盐，
-- 同一密码哈希也不同。测试账号见 README（admin/admin123，其余 123456）。
-- 仅在 users 为空时由 init_db.py 执行，避免重复写入
USE campus_water;

INSERT INTO users (username, salt, password_hash, real_name, role, status) VALUES
('admin', '567262a6f5ca19751d43c5557122a99a', '985afe03da9f4d1745e729d4dbaaeed633e9a26cf89048ba297ca1c5f4a19a01', 'wd', 'admin', 'active'),
('inspector1', '6d003281eebf6ccbf836ea4ca93b80c2', '60ce3e358671d98a6930c2853b8b69f70ab484e1aa579ac4d2ce857454237cb5', 'wzl', 'inspector', 'active'),
('inspector2', '257fdec77c2cf65bf33cb7584247cb4f', '2d7b0d76d584da391b9df7b39932227de09ea193b239523e04de71d868e09f42', 'lyz', 'inspector', 'active'),
('reviewer', 'dd06b948575f0175538fa7082c6ac427', '5dbb8fcf269452185d5966c517a535c7c7a4b0e96ee6b7c2a3759bd65b1414f9', '审核员', 'reviewer', 'active'),
('admin2', 'afa1dae20f8597244be9cacecd7a325a', '4c91fa8e7d41f50fe5679dc33deab266540935dc391f6030e556cb05e1c0ee86', '管理员', 'admin', 'active');

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
