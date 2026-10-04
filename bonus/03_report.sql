-- 전체 샘플 기간 2026-09-01~2026-10-04. 매출은 completed 주문의 수량*주문 당시 단가다.
-- M01 | 월별 완료 주문 건수와 매출: 취소·접수 주문을 제외하고 주문 중복 집계를 방지한다.
-- SQLite substr()로 ISO 8601 시각에서 YYYY-MM 부분을 추출한다.
SELECT substr(o.ordered_at, 1, 7) AS order_month,
       COUNT(DISTINCT o.order_id) AS completed_order_count,
       SUM(i.quantity * i.unit_price) AS sales_amount
FROM cafe_order AS o
INNER JOIN order_item AS i ON i.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY substr(o.ordered_at, 1, 7)
ORDER BY order_month;

-- M02 | 판매량 TOP 5: 완료 주문의 메뉴별 총수량, 동률이면 menu_id 오름차순이다.
SELECT m.menu_id, m.name, SUM(i.quantity) AS sold_quantity,
       SUM(i.quantity * i.unit_price) AS sales_amount
FROM menu AS m
INNER JOIN order_item AS i ON i.menu_id = m.menu_id
INNER JOIN cafe_order AS o ON o.order_id = i.order_id
WHERE o.status = 'completed'
GROUP BY m.menu_id, m.name
ORDER BY sold_quantity DESC, m.menu_id
LIMIT 5;

-- M03 | 기간 내 반복 구매 고객 비율(%): 완료 주문 2회 이상 고객 / 1회 이상 고객 * 100.
-- 100.0은 정수 나눗셈을 피한다. 구매 고객이 0명이면 비율은 NULL(정의 불가)이다.
SELECT COUNT(*) AS purchasing_customers,
       COALESCE(SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END), 0) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END)
             / NULLIF(COUNT(*), 0), 2) AS repeat_customer_rate_percent
FROM (
    SELECT customer_id, COUNT(*) AS order_count
    FROM cafe_order
    WHERE status = 'completed'
    GROUP BY customer_id
) AS customer_orders;
