-- 补建缺失的数据表
-- 执行方式: mysql -u root -p123456 lele_park < Project/scripts/create_missing_tables.sql

CREATE TABLE IF NOT EXISTS ticket_orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(32) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    total_amount FLOAT NOT NULL,
    pay_amount FLOAT NOT NULL,
    discount_amount FLOAT DEFAULT 0,
    pay_method VARCHAR(10) DEFAULT 'wechat',
    pay_status VARCHAR(15) DEFAULT 'unpaid',
    visit_date DATE NOT NULL,
    status VARCHAR(15) DEFAULT 'pending',
    qr_code VARCHAR(500),
    used_at DATETIME,
    cancelled_at DATETIME,
    refund_amount FLOAT,
    refund_reason VARCHAR(200),
    remark VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_no (order_no),
    INDEX idx_user (user_id),
    INDEX idx_visit_date (visit_date),
    INDEX idx_pay_status (pay_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ticket_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    ticket_type_id BIGINT NOT NULL,
    quantity INT DEFAULT 1,
    unit_price FLOAT NOT NULL,
    subtotal FLOAT NOT NULL,
    visitor_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS queue_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    queue_number INT NOT NULL,
    queue_date DATE NOT NULL,
    status VARCHAR(15) DEFAULT 'waiting',
    taken_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    called_at DATETIME,
    completed_at DATETIME,
    cancelled_at DATETIME,
    INDEX idx_user_date (user_id, queue_date),
    INDEX idx_project_date (project_id, queue_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS members (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT UNIQUE NOT NULL,
    member_no VARCHAR(20) UNIQUE NOT NULL,
    level INT DEFAULT 1,
    points INT DEFAULT 0,
    total_points INT DEFAULT 0,
    balance FLOAT DEFAULT 0,
    card_type VARCHAR(10) DEFAULT 'none',
    card_expire DATE,
    join_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS point_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    points INT NOT NULL,
    balance_after INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    description VARCHAR(200),
    related_order VARCHAR(32),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS community_posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    images JSON,
    post_type VARCHAR(15) DEFAULT 'travelogue',
    related_project BIGINT,
    tags JSON,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    status VARCHAR(15) DEFAULT 'published',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_type (post_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS post_reviews (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    parent_id BIGINT,
    content TEXT NOT NULL,
    like_count INT DEFAULT 0,
    status VARCHAR(15) DEFAULT 'visible',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(15) NOT NULL,
    related_id VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    channel VARCHAR(10) DEFAULT 'app',
    sent_at DATETIME,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_read (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    operator_id BIGINT,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id VARCHAR(50),
    detail JSON,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_operator (operator_id),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
