-- 평가 보완용 추가 실습. 스키마와 시드를 넣은 새 DB에서 번호 순서로 실행한다.
-- E02/E03은 의도한 오류다. 도우미는 오류를 기록한 뒤 다음 블록으로 진행한다.
PRAGMA foreign_keys = ON; -- SQLite 전용

-- E01 | 행 수 증명: 샘플 입력 직후 네 테이블의 COUNT(*)를 확인한다.
SELECT 'customer' AS table_name, COUNT(*) AS row_count FROM customer
UNION ALL SELECT 'menu', COUNT(*) FROM menu
UNION ALL SELECT 'cafe_order', COUNT(*) FROM cafe_order
UNION ALL SELECT 'order_item', COUNT(*) FROM order_item;

-- E02 | 부모 삭제 제한: 주문이 남아 있는 고객 1의 삭제를 FK가 차단한다.
-- EXPECT_ERROR: FOREIGN KEY constraint failed
DELETE FROM customer WHERE customer_id = 1;

-- E03 | PK 중복 제한: 이미 존재하는 customer_id=1의 재입력을 차단한다.
-- EXPECT_ERROR: UNIQUE constraint failed: customer.customer_id
INSERT INTO customer (customer_id, name, email, joined_on)
VALUES (1, '중복키실습', 'duplicate-key@example.com', '2026-10-04');

-- E04 | INNER JOIN 비교: 고객 1과 11 중 주문과 연결된 고객 1의 3개 행만 조회된다.
SELECT c.customer_id, c.name, o.order_id
FROM customer AS c
INNER JOIN cafe_order AS o ON o.customer_id = c.customer_id
WHERE c.customer_id IN (1, 11)
ORDER BY c.customer_id, o.order_id;

-- E05 | LEFT JOIN 비교: 같은 조건에서 주문 없는 고객 11도 order_id=NULL로 남는다.
SELECT c.customer_id, c.name, o.order_id
FROM customer AS c
LEFT JOIN cafe_order AS o ON o.customer_id = c.customer_id
WHERE c.customer_id IN (1, 11)
ORDER BY c.customer_id, o.order_id;

-- E06 | 집계 경계: 빈 입력의 COUNT=0, SUM/AVG=NULL이며 0은 집계에 포함된다.
SELECT COUNT(*) AS row_count, SUM(quantity) AS quantity_sum,
       AVG(quantity) AS quantity_average,
       COALESCE(SUM(quantity), 0) AS display_sum
FROM order_item WHERE order_id = 999;
SELECT COUNT(*) AS all_rows, COUNT(value) AS nonnull_rows,
       COUNT(DISTINCT value) AS distinct_nonnull_values,
       SUM(value) AS value_sum, AVG(value) AS value_average
FROM (SELECT 0 AS value UNION ALL SELECT 0 UNION ALL SELECT NULL) AS sample;
