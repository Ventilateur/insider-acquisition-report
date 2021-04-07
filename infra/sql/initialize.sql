CREATE TABLE IF NOT EXISTS sec4_transactions (
    transaction_date DATE NOT NULL,
    company_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(1024) NOT NULL,
    insiders JSON NOT NULL,
    buy_or_sell ENUM('B', 'S') NOT NULL,
    price DECIMAL(10, 5) NOT NULL,
    nb_shares INTEGER NOT NULL,
    security_title VARCHAR(255) NOT NULL,
    sec4_file_location VARCHAR(1024) NOT NULL
);

CREATE INDEX idx_transaction_date ON sec4_transactions (transaction_date);
CREATE INDEX idx_company_code ON sec4_transactions (company_code);
CREATE INDEX idx_buy_or_sell ON sec4_transactions (buy_or_sell);

CREATE TABLE IF NOT EXISTS sec4_unprocessed_files (
    file VARCHAR(1024) NOT NULL UNIQUE
)