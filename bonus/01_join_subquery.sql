-- 새 샘플 DB에서 실행. 요구: 완료 주문이 있는 고객을 중복 없이 조회한다.
-- B01 | JOIN 방식: 주문 수만큼 생기는 중복 고객을 DISTINCT로 제거한다.
SELECT DISTINCT c.customer_id, c.name
FROM customer AS c
INNER JOIN cafe_order AS o ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
ORDER BY c.customer_id;

-- B02 | 서브쿼리 방식: EXISTS로 완료 주문 존재 여부만 확인한다.
SELECT c.customer_id, c.name
FROM customer AS c
WHERE EXISTS (
    SELECT 1 FROM cafe_order AS o
    WHERE o.customer_id = c.customer_id AND o.status = 'completed'
)
ORDER BY c.customer_id;
