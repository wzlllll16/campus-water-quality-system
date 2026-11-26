-- 校园水质生态监测与巡检管护管理系统 — 建库建表
-- MySQL 5.5 / 8 / MariaDB 兼容，字符集 utf8mb4
-- 兼容说明：MySQL 5.5 不支持 DATETIME DEFAULT CURRENT_TIMESTAMP（5.6.5 才支持），
-- 所以时间列改用 TIMESTAMP DEFAULT CURRENT_TIMESTAMP；anomalies.updated_at 单独用 DATETIME
-- 加一个固定默认值，程序和演示数据都会显式写入 updated_at，不依赖数据库默认值。
-- 执行方式：python init_db.py（会先建库再建表）
CREATE DATABASE IF NOT EXISTS campus_water CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_water;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL COMMENT 'PBKDF2-HMAC-SHA256 哈希，64 位 hex',
    salt CHAR(32) NOT NULL COMMENT '每用户随机 16 字节盐的 hex，每次改密码重新生成',
    real_name VARCHAR(50) NOT NULL,
    role ENUM('admin','inspector','reviewer') NOT NULL COMMENT 'admin=系统管理员, inspector=巡检员, reviewer=审核员',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_role (role),
    INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 监测点位台账
CREATE TABLE IF NOT EXISTS monitoring_points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '点位编号，如 JD001',
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL COMMENT '湖泊/景观水池/绿化带',
    location VARCHAR(200) NOT NULL,
    manager VARCHAR(50) NOT NULL COMMENT '负责人',
    status ENUM('启用','停用') NOT NULL DEFAULT '启用',
    archived TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0未归档 1已归档',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_points_type (type),
    INDEX idx_points_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 监测数据
CREATE TABLE IF NOT EXISTS measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_id INT NOT NULL,
    measure_date DATE NOT NULL,
    temperature DECIMAL(5,1) NULL,
    ph DECIMAL(4,2) NOT NULL,
    dissolved_oxygen DECIMAL(5,2) NOT NULL COMMENT 'mg/L',
    turbidity DECIMAL(6,2) NOT NULL COMMENT 'NTU',
    ammonia DECIMAL(5,2) NOT NULL COMMENT 'mg/L',
    recorder VARCHAR(50) NOT NULL,
    result ENUM('正常','超标') NOT NULL,
    remark VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (point_id) REFERENCES monitoring_points(id) ON DELETE CASCADE,
    INDEX idx_meas_point (point_id),
    INDEX idx_meas_date (measure_date),
    INDEX idx_meas_result (result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 巡检任务
CREATE TABLE IF NOT EXISTS inspection_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    cycle VARCHAR(20) NOT NULL COMMENT '每天/每周/每月',
    assignee VARCHAR(50) NOT NULL,
    planned_date DATE NOT NULL,
    status ENUM('待巡检','巡检中','已完成','已逾期') NOT NULL DEFAULT '待巡检',
    result VARCHAR(255) NOT NULL DEFAULT '',
    inspect_time DATE NULL,
    remark VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (point_id) REFERENCES monitoring_points(id) ON DELETE CASCADE,
    INDEX idx_task_point (point_id),
    INDEX idx_task_status (status),
    INDEX idx_task_planned (planned_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 异常记录
CREATE TABLE IF NOT EXISTS anomalies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL COMMENT '水质超标/设施损坏/其他隐患',
    description VARCHAR(500) NOT NULL,
    status ENUM('待审核','已驳回','待整改','待复查','已归档') NOT NULL DEFAULT '待审核',
    reporter VARCHAR(50) NOT NULL,
    reviewer VARCHAR(50) NOT NULL DEFAULT '',
    review_comment VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT '2000-01-01 00:00:00',
    FOREIGN KEY (point_id) REFERENCES monitoring_points(id) ON DELETE CASCADE,
    INDEX idx_anom_point (point_id),
    INDEX idx_anom_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 设备台账
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL COMMENT '水质传感器/水泵/增氧机',
    point_id INT NULL,
    install_date DATE NOT NULL,
    next_maintenance_date DATE NOT NULL,
    status ENUM('正常','故障','维修中','报废') NOT NULL DEFAULT '正常',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (point_id) REFERENCES monitoring_points(id) ON DELETE SET NULL,
    INDEX idx_devices_type (type),
    INDEX idx_devices_next (next_maintenance_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 维保日志
CREATE TABLE IF NOT EXISTS maintenance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    type VARCHAR(20) NOT NULL COMMENT '定期维保/维修/故障处理',
    content VARCHAR(500) NOT NULL,
    maintainer VARCHAR(50) NOT NULL,
    maintain_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_maint_device (device_id),
    INDEX idx_maint_date (maintain_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 档案表（按年度/点位汇总后写入）
CREATE TABLE IF NOT EXISTS archives (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL,
    point_id INT NOT NULL,
    record_count INT NOT NULL DEFAULT 0 COMMENT '该年度该点位监测记录数',
    exceed_count INT NOT NULL DEFAULT 0,
    summary VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (point_id) REFERENCES monitoring_points(id) ON DELETE CASCADE,
    UNIQUE KEY uk_archive_year_point (year, point_id),
    INDEX idx_archives_year (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. 系统日志
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    detail VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_logs_user (username),
    INDEX idx_logs_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
