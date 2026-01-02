-- Database schema for Billing System

-- Table: meter_readings
CREATE TABLE IF NOT EXISTS meter_readings (
    id SERIAL PRIMARY KEY,
    meter_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    reading_value DECIMAL(10, 2) NOT NULL,
    reading_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_meter_id (meter_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_reading_date (reading_date)
);

-- Table: bills
CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    meter_id VARCHAR(100) NOT NULL,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    consumption_kwh DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_link TEXT,
    payment_link_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_meter_id (meter_id),
    INDEX idx_status (status)
);

-- Table: notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    customer_id VARCHAR(100) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    whatsapp_message_id VARCHAR(255),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bill_id (bill_id),
    INDEX idx_customer_id (customer_id)
);

-- Sample data for testing
-- INSERT INTO meter_readings (meter_id, customer_id, reading_value, reading_date)
-- VALUES 
--     ('METER001', 'CUST001', 1000.00, '2025-10-01'),
--     ('METER001', 'CUST001', 1150.50, '2025-11-01');
