CREATE DATABASE IF NOT EXISTS cod_db;
USE cod_db;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

CREATE TABLE IF NOT EXISTS shopify_stores (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    shop_url VARCHAR(255) UNIQUE NOT NULL,
    access_token TEXT NOT NULL,
    api_version VARCHAR(20) NOT NULL DEFAULT '2023-10',
    cod_tags VARCHAR(255) NOT NULL DEFAULT 'post office',
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_shop_url (shop_url)
);

CREATE TABLE IF NOT EXISTS cod_orders (
    id BIGINT PRIMARY KEY,
    shop_id BIGINT NOT NULL,
    name VARCHAR(64) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    phone VARCHAR(64),
    address1 VARCHAR(255),
    address2 VARCHAR(255),
    city VARCHAR(128),
    province VARCHAR(128),
    country VARCHAR(128),
    postal_code VARCHAR(32),
    total_price DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    financial_status VARCHAR(50),
    fulfillment_status VARCHAR(50),
    tags TEXT,
    created_at_utc DATETIME NOT NULL,
    updated_at_utc DATETIME NOT NULL,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shopify_stores(id),
    INDEX idx_shop_created (shop_id, created_at_utc),
    INDEX idx_shop_updated (shop_id, updated_at_utc)
);

CREATE TABLE IF NOT EXISTS money_order_pdfs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES cod_orders(id),
    INDEX idx_order (order_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    actor VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_action (action, created_at)
);