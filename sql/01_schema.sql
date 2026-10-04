-- 카페 주문 관리 / SQLite / 새 DB에서 실행한다.
-- SQLite 전용: FK 검사는 연결마다 켜야 하며 트랜잭션 시작 전에 설정한다.
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    joined_on TEXT NOT NULL  -- SQLite: 날짜는 ISO 8601 YYYY-MM-DD TEXT로 저장한다.
);

CREATE TABLE menu (
    menu_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('coffee', 'tea', 'drink', 'bakery')),
    -- SQLite는 동적 타입이므로 typeof()로 원 단위 정수까지 확인한다.
    price INTEGER NOT NULL CHECK (typeof(price) = 'integer' AND price > 0),
    is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1))
);

CREATE TABLE cafe_order (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    ordered_at TEXT NOT NULL, -- ISO 8601 YYYY-MM-DD HH:MM:SS, 한국 현지 시각
    status TEXT NOT NULL CHECK (status IN ('placed', 'completed', 'cancelled')),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT
);

CREATE TABLE order_item (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    menu_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (typeof(quantity) = 'integer' AND quantity > 0),
    -- 주문 당시 단가를 보존한다. 메뉴 가격이 바뀌어도 과거 주문 금액은 유지된다.
    unit_price INTEGER NOT NULL CHECK (typeof(unit_price) = 'integer' AND unit_price > 0),
    UNIQUE (order_id, menu_id),
    FOREIGN KEY (order_id) REFERENCES cafe_order(order_id) ON DELETE RESTRICT,
    FOREIGN KEY (menu_id) REFERENCES menu(menu_id) ON DELETE RESTRICT
);

COMMIT;
