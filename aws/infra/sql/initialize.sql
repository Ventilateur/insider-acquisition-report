CREATE TABLE sec4_transactions (
    transaction_date DATE NOT NULL,
    company_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(1024) NOT NULL,
    insiders JSON NOT NULL,
    buy_or_sell ENUM('B', 'S') NOT NULL,
    price DECIMAL(10, 5) NOT NULL,
    nb_shares INTEGER NOT NULL,
    security_title VARCHAR(255) NOT NULL,
    sec4_file_location VARCHAR(1024) NOT NULL,
    sec4_file_date DATE NOT NULL
);

CREATE INDEX idx_transaction_date ON sec4_transactions (transaction_date);
CREATE INDEX idx_sec4_file_date ON sec4_transactions (sec4_file_date);
CREATE INDEX idx_company_code ON sec4_transactions (company_code);
CREATE INDEX idx_buy_or_sell ON sec4_transactions (buy_or_sell);

CREATE TABLE sec4_query_states (
    query_date DATE PRIMARY KEY,
    completed BOOLEAN NOT NULL
)