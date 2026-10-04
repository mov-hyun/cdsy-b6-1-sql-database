-- 각 B번호 블록을 따로 실행한다. B03은 의도한 실패이며 B04까지 실행하려면 계속 진행한다.
-- 실행 도우미는 예상된 오류를 기록하고 다음 블록으로 진행한다.
PRAGMA foreign_keys = ON; -- SQLite 전용, 트랜잭션 바깥에서 설정

-- B03 | FK 위반: 존재하지 않는 고객 999를 참조하는 주문 입력은 차단되어야 한다.
-- EXPECT_ERROR: FOREIGN KEY constraint failed
INSERT INTO cafe_order (order_id, customer_id, ordered_at, status)
VALUES (99, 999, '2026-10-04 12:00:00', 'placed');

-- B04 | 수정: 존재하는 고객 1을 참조하면 입력 가능하다. 실습 후 ROLLBACK으로 복구한다.
BEGIN TRANSACTION;
INSERT INTO cafe_order (order_id, customer_id, ordered_at, status)
VALUES (99, 1, '2026-10-04 12:00:00', 'placed');
SELECT order_id, customer_id, status FROM cafe_order WHERE order_id = 99;
ROLLBACK;
SELECT COUNT(*) AS remaining_practice_orders FROM cafe_order WHERE order_id = 99;
