-- 01_schema.sql -> 02_seed.sql -> 이 파일을 위에서부터 한 번 실행한다.
-- Q01~Q15: 핵심 SQL 15개. Q16: 추가 인덱스 실습.
-- Q14/Q15는 변경 전후 확인 SELECT를 포함하는 하나의 실습 단위다.
-- SQLite 전용: PRAGMA, changes(), EXPLAIN QUERY PLAN.
-- LIMIT는 SQLite/MySQL/PostgreSQL에서 지원하며 표준 FETCH 문법과 다르다.
PRAGMA foreign_keys = ON;

-- Q01 | 기본 조회: 판매 중인 커피 메뉴를 가격 오름차순으로 확인한다.
SELECT menu_id, name, price
FROM menu
WHERE category = 'coffee' AND is_available = 1
ORDER BY price, menu_id;

-- Q02 | 기본 조회: 2026년 9월에 가입한 고객을 최근 가입 순으로 확인한다.
SELECT customer_id, name, joined_on
FROM customer
WHERE joined_on >= '2026-09-01' AND joined_on < '2026-10-01'
ORDER BY joined_on DESC, customer_id;

-- Q03 | 기본 조회: 최근 완료 주문 5개를 확인한다.
SELECT order_id, customer_id, ordered_at
FROM cafe_order
WHERE status = 'completed'
ORDER BY ordered_at DESC, order_id DESC
LIMIT 5;

-- Q04 | 기본 조회: 이름에 라테가 포함된 메뉴를 검색한다.
SELECT menu_id, name, price
FROM menu
WHERE name LIKE '%라테%'
ORDER BY menu_id;

-- Q05 | INNER JOIN: 주문에 고객 이름을 연결해 주문 이력을 확인한다.
SELECT o.order_id, c.name AS customer_name, o.ordered_at, o.status
FROM cafe_order AS o
INNER JOIN customer AS c ON c.customer_id = o.customer_id
ORDER BY o.order_id;

-- Q06 | INNER JOIN: 1번 주문의 메뉴, 수량, 주문 당시 단가와 항목 금액을 확인한다.
SELECT i.order_item_id, m.name AS menu_name, i.quantity, i.unit_price,
       i.quantity * i.unit_price AS line_amount
FROM order_item AS i
INNER JOIN menu AS m ON m.menu_id = i.menu_id
WHERE i.order_id = 1
ORDER BY i.order_item_id;

-- Q07 | LEFT JOIN: 어떤 상태의 주문도 없는 고객을 확인한다.
SELECT c.customer_id, c.name
FROM customer AS c
LEFT JOIN cafe_order AS o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL
ORDER BY c.customer_id;

-- Q08 | 다중 INNER JOIN: 10월 완료 주문의 고객과 구매 메뉴를 한 번에 확인한다.
SELECT o.order_id, c.name AS customer_name, m.name AS menu_name,
       i.quantity, i.quantity * i.unit_price AS line_amount
FROM cafe_order AS o
INNER JOIN customer AS c ON c.customer_id = o.customer_id
INNER JOIN order_item AS i ON i.order_id = o.order_id
INNER JOIN menu AS m ON m.menu_id = i.menu_id
WHERE o.status = 'completed'
  AND o.ordered_at >= '2026-10-01 00:00:00'
  AND o.ordered_at < '2026-11-01 00:00:00'
ORDER BY o.order_id, i.order_item_id;

-- Q09 | 집계 COUNT: 고객별 완료 주문 건수를 집계하며 구매 없는 고객도 0으로 표시한다.
SELECT c.customer_id, c.name, COUNT(o.order_id) AS completed_order_count
FROM customer AS c
LEFT JOIN cafe_order AS o
    ON o.customer_id = c.customer_id AND o.status = 'completed'
GROUP BY c.customer_id, c.name
ORDER BY completed_order_count DESC, c.customer_id;

-- Q10 | 집계 SUM: 완료 주문에서 메뉴별 판매 수량과 매출을 집계한다.
SELECT m.menu_id, m.name, SUM(i.quantity) AS sold_quantity,
       SUM(i.quantity * i.unit_price) AS sales_amount
FROM menu AS m
INNER JOIN order_item AS i ON i.menu_id = m.menu_id
INNER JOIN cafe_order AS o ON o.order_id = i.order_id
WHERE o.status = 'completed'
GROUP BY m.menu_id, m.name
ORDER BY sold_quantity DESC, m.menu_id;

-- Q11 | 집계 AVG: 고객별 완료 주문의 평균 주문 금액을 구한다(상세 항목 평균과 구분).
SELECT c.customer_id, c.name, COUNT(*) AS completed_order_count,
       ROUND(AVG(t.order_amount), 2) AS average_order_amount
FROM customer AS c
INNER JOIN (
    SELECT o.order_id, o.customer_id,
           SUM(i.quantity * i.unit_price) AS order_amount
    FROM cafe_order AS o
    INNER JOIN order_item AS i ON i.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.order_id, o.customer_id
) AS t ON t.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;

-- Q12 | 서브쿼리: 판매 중인 메뉴의 평균 가격보다 비싼 판매 중 메뉴를 확인한다.
SELECT menu_id, name, price
FROM menu
WHERE is_available = 1
  AND price > (SELECT AVG(price) FROM menu WHERE is_available = 1)
ORDER BY price DESC, menu_id;

-- Q13 | 서브쿼리 NOT EXISTS: 완료 주문에서 한 번도 판매되지 않은 메뉴를 찾는다.
SELECT m.menu_id, m.name
FROM menu AS m
WHERE NOT EXISTS (
    SELECT 1
    FROM order_item AS i
    INNER JOIN cafe_order AS o ON o.order_id = i.order_id
    WHERE i.menu_id = m.menu_id AND o.status = 'completed'
)
ORDER BY m.menu_id;

-- Q14 | UPDATE: 아메리카노 현재 가격을 3,200원으로 바꾸고 과거 주문 단가 보존을 확인한다.
SELECT menu_id, name, price FROM menu WHERE menu_id = 1;
UPDATE menu SET price = 3200 WHERE menu_id = 1;
SELECT changes() AS updated_rows; -- SQLite 전용: 직전 DML의 변경 행 수
SELECT menu_id, name, price FROM menu WHERE menu_id = 1;
SELECT order_item_id, order_id, unit_price
FROM order_item WHERE menu_id = 1 ORDER BY order_item_id;

-- Q15 | DELETE: 주문 없는 삭제실습고객만 삭제한다(고객 수 12 -> 11).
SELECT customer_id, name FROM customer WHERE customer_id = 12;
DELETE FROM customer
WHERE customer_id = 12
  AND NOT EXISTS (SELECT 1 FROM cafe_order WHERE customer_id = 12);
SELECT changes() AS deleted_rows; -- SQLite 전용
SELECT customer_id, name FROM customer WHERE customer_id = 12;
SELECT COUNT(*) AS remaining_customers FROM customer;

-- Q16 | 인덱스: 고객별 주문 검색과 시간순 정렬을 위해 (customer_id, ordered_at)에 생성한다.
-- SQLite 전용 EXPLAIN QUERY PLAN으로 전후 접근 방식을 확인하며 속도 향상을 단정하지 않는다.
EXPLAIN QUERY PLAN
SELECT order_id, ordered_at FROM cafe_order
WHERE customer_id = 1 ORDER BY ordered_at;
CREATE INDEX idx_cafe_order_customer_time ON cafe_order(customer_id, ordered_at);
EXPLAIN QUERY PLAN
SELECT order_id, ordered_at FROM cafe_order
WHERE customer_id = 1 ORDER BY ordered_at;
SELECT order_id, ordered_at FROM cafe_order
WHERE customer_id = 1 ORDER BY ordered_at;
