# 설계 이유와 학습 정리

## 엑셀과 관계형 DB

관계형 DB는 테이블 사이의 참조와 데이터 규칙을 선언하고, 여러 작업에서 일관되게 강제한다.
이 과제에서는 존재하지 않는 고객의 주문, 중복 이메일, 0개 수량을 DB가 거부한다.
엑셀도 표·조회 함수·데이터 모델로 데이터를 연결할 수 있다. 핵심 학습점은 DB가 PK/FK,
제약조건, 트랜잭션과 SQL을 통해 관계와 무결성을 관리하는 방식이다.

예를 들어 엑셀의 주문 목록에 고객 이메일까지 반복해서 적으면 다음 상황을 별도로 관리해야 한다.

| 상황 | 엑셀에서 직접 관리할 작업 | 이 DB의 처리 |
|---|---|---|
| 고객01의 이메일 변경 | 여러 주문 행의 이메일 수정 또는 고객 시트 조회식 관리 | customer의 한 행을 수정하고 JOIN으로 조회 |
| 고객999로 주문 입력 | 목록 유효성 검사·조회식과 입력 경로 관리 | FK가 없는 고객 참조를 차단([B03](../results/b03.txt)) |
| 주문이 있는 고객 삭제 | 관련 주문 시트의 참조 확인 | RESTRICT가 삭제 차단([E02](../results/e02.txt)) |

엑셀에서도 유효성 검사와 조회식을 구성할 수 있다. 여기서는 같은 규칙을 DB 제약조건으로 선언한다.

## 왜 네 테이블로 나누었나

주문마다 고객 이메일과 메뉴 이름을 복사하면 이메일 변경 시 여러 행을 고쳐야 한다.
고객과 메뉴는 각 테이블에서 한 번 관리하고 주문에서는 ID로 참조한다.
한 주문에 메뉴가 여러 개 들어가므로 주문 정보와 상세를 분리한다.

주문 금액은 `SUM(quantity * unit_price)`로 구한다. 주문 테이블에 총액을 중복 저장하지 않아
수량 변경과 저장 총액이 어긋날 가능성을 줄인다.
메뉴의 `price`는 현재 가격이고 상세의 `unit_price`는 주문 당시 가격이다.
서로 다른 시점의 사실이므로 둘 다 저장한다. Q14에서 과거 단가 보존을 실제로 확인한다.

정규화의 기본 개념과 연결하면 다음과 같다. 이번 도메인에서 가정한 데이터 의존관계에 대한 설명이다.

| 단계 | 이 설계에 적용한 내용 |
|---|---|
| 1NF | 한 셀에 메뉴 목록을 넣지 않고 order_item 한 행에 메뉴 한 종류와 수량을 저장한다. |
| 2NF | 상세의 자연키 (order_id, menu_id) 중 order_id에만 달린 주문시각·고객은 cafe_order에 둔다. 메뉴 이름은 menu에 둔다. |
| 3NF | order_id → customer_id → email로 이어지는 고객 속성을 customer에서 관리해 주문에 반복 저장하지 않는다. |

정규화 단계 이름보다 어떤 사실을 어느 테이블이 책임지는지에 초점을 맞춘다.

## 키와 제약조건

| 규칙 | 적용 | 의미 |
|---|---|---|
| PK | 네 테이블의 ID | 한 행을 유일하게 구분 |
| FK | 주문.customer_id | 존재하는 고객의 주문만 허용 |
| FK | 상세.order_id, 상세.menu_id | 존재하는 주문·메뉴에만 상세 연결 |
| NOT NULL | 필수 이름·참조·수량·가격 등 | 필수 값 누락 차단 |
| UNIQUE | 고객.email, 메뉴.name | 중복 등록 차단 |
| 복합 UNIQUE | 상세(order_id, menu_id) | 같은 주문의 같은 메뉴는 수량으로 합산 |
| CHECK | 양의 정수 수량·가격, 허용된 상태·분류, 0/1 | 잘못된 값 입력 차단 |
| ON DELETE RESTRICT | 세 FK | 자식이 남아 있는 부모 삭제 차단 |

SQLite에서 `INTEGER PRIMARY KEY`는 행 식별자와 연결되는 특별한 선언이다.
샘플은 관계를 읽기 쉽게 ID를 명시하며 별도 AUTOINCREMENT는 사용하지 않는다.
ID를 생략한 INSERT에서는 SQLite가 INTEGER PRIMARY KEY 값을 배정할 수 있다.
이 과제의 샘플 입력은 네 테이블 모두 명시적 ID를 사용하므로 실행마다 같은 관계를 재현한다.
문자열 길이와 날짜의 완전한 유효성, 상태 전이, 완료 주문에 상세가 반드시 존재해야 한다는 규칙은
이 스키마가 강제하지 않는다. 실제 서비스로 확장할 때 따로 설계할 부분이다.

관계별 동작 예시는 다음과 같다.

- 고객→주문: 고객 1은 주문 1·3·13을 가진다. 고객 999의 주문 입력은 실패하고, 고객 1 삭제도 자식 주문 때문에 실패한다.
- 주문→상세: 주문 1에 메뉴 2의 상세를 추가할 수 있다. 기존 메뉴 1을 새 행으로 중복 추가하면 복합 UNIQUE가 막으므로 기존 행의 수량을 수정한다.
- 메뉴→상세: 메뉴 1은 여러 주문상세에서 참조한다. 현재 가격 수정은 가능하며 과거 unit_price는 유지된다. 참조 중인 메뉴 삭제는 FK가 막는다.

직접 확인할 수 있는 PK/FK 예시:

```sql
-- 새 샘플 DB에서 각 문장을 개별 실행한다. 아래 세 문장은 의도적으로 실패한다.
PRAGMA foreign_keys = ON;
INSERT INTO customer (customer_id, name, email, joined_on)
VALUES (1, '중복키실습', 'duplicate-key@example.com', '2026-10-04');
-- 결과: UNIQUE constraint failed: customer.customer_id (E03)
INSERT INTO cafe_order (order_id, customer_id, ordered_at, status)
VALUES (99, 999, '2026-10-04 12:00:00', 'placed');
-- 결과: FOREIGN KEY constraint failed (B03)
DELETE FROM customer WHERE customer_id = 1;
-- 결과: FOREIGN KEY constraint failed (E02)
```

실제 로그·캡처: [PK 중복](../results/screenshots/e03.png), [없는 부모 참조](../results/screenshots/b03.png),
[참조 중인 부모 삭제](../results/screenshots/e02.png). 정정 INSERT와 복구는 [B04](../results/b04.txt)에 있다.

## SQL을 어떻게 구분하나

- `INSERT`: 새 고객, 메뉴, 주문, 상세를 저장한다. 부모부터 입력한다.
- `SELECT`: 기존 데이터에서 조건에 맞는 행과 컬럼을 읽는다.
- `UPDATE`: 특정 행의 값을 변경한다. Q14는 menu_id=1만 수정한다.
- `DELETE`: 특정 행을 삭제한다. Q15는 주문 없는 실습 고객 12만 삭제한다.
- `JOIN`: 키가 같은 행을 연결한다. Q06은 상세에 메뉴 이름을 붙인다.
- `GROUP BY`: 같은 기준의 행을 묶는다. Q10은 메뉴별 수량과 매출을 더한다.

`INNER JOIN`은 양쪽에 연결된 행만 반환한다. `LEFT JOIN`은 왼쪽 행을 유지하고,
상대가 없으면 오른쪽 컬럼이 NULL이다. Q07은 이 NULL로 주문 없는 고객을 찾는다.

같은 고객 1·11을 대상으로 비교한 [INNER 캡처](../results/screenshots/e04.png)는 주문 3행을,
[LEFT 캡처](../results/screenshots/e05.png)는 고객 11의 NULL 행까지 4행을 보여준다.

Q09에서 완료 상태 조건을 `ON`에 넣어 구매 없는 고객도 유지한다.
`COUNT(o.order_id)`는 연결된 주문만 세므로 주문 없는 고객은 0이다.
`COUNT(*)`로 바꾸면 LEFT JOIN이 남긴 고객 행을 세어 1이 되므로 목적과 달라진다.

주문과 상세를 조인하면 주문 한 건이 상세 개수만큼 반복된다.
월별 주문 건수는 `COUNT(DISTINCT order_id)`로 세고, 평균 주문 금액은 주문별 금액부터 만든 후 평균낸다.
`AVG(quantity * unit_price)`를 바로 쓰면 상세 항목의 평균 금액이 된다.

NULL과 0은 구분한다. `COUNT(*)`는 모든 행, `COUNT(컬럼)`은 NULL이 아닌 값,
`COUNT(DISTINCT 컬럼)`은 중복과 NULL을 제외한 값을 센다. SUM/AVG도 NULL을 제외하며 0은 포함한다.
입력 행이 없으면 COUNT는 0, SUM/AVG는 NULL이다. 표시 목적의 합계에는 `COALESCE(SUM(...), 0)`를
쓸 수 있지만, 분모가 0인 비율은 NULL로 두어 정의 불가를 표시한다.
[E06 실제 결과](../results/e06.txt)와 [이미지](../results/screenshots/e06.png)에서 두 경계를 비교했다.

## 대표 복잡 쿼리 Q11의 처리 순서

1. `cafe_order`와 `order_item`을 연결하고 completed 주문만 남긴다.
2. 내부 쿼리에서 order_id와 customer_id로 묶어 주문별 `SUM(quantity * unit_price)`를 계산한다.
   고객01의 주문 1·3·13은 각각 9,500원·9,000원·12,000원이다.
3. 외부 쿼리에서 고객별로 묶어 주문 건수와 주문 금액 평균을 구한다.
   고객01은 3건, `(9,500 + 9,000 + 12,000) / 3 = 10,166.67원`이다.

전체 SQL과 결과는 [Q11 텍스트](../results/q11.txt), [Q11 캡처](../results/screenshots/q11.png)에 있다.

## 인덱스

Q16의 `(customer_id, ordered_at)` 인덱스는 고객 ID로 범위를 좁힌 뒤 주문시각 순으로 읽는 조회를 돕는다.
컬럼 순서가 중요하다. 고객 조건 없이 주문시각만 검색하는 요구에는 다른 인덱스가 더 적합할 수 있다.
인덱스는 저장 공간을 사용하며 입력·수정 시 갱신 비용이 생긴다.
이 과제에서는 실행 계획의 접근 방식만 비교하며, 작은 데이터로 처리 시간 개선을 주장하지 않는다.

실제 [Q16 로그](../results/q16.txt)와 [전후 실행계획 캡처](../results/screenshots/q16.png)의 차이:

| 시점 | 실행계획 detail | 해석 |
|---|---|---|
| 생성 전 | SCAN cafe_order / USE TEMP B-TREE FOR ORDER BY | 테이블을 훑고 정렬용 임시 구조 사용 |
| 생성 후 | SEARCH cafe_order USING COVERING INDEX idx_cafe_order_customer_time (customer_id=?) | 고객 범위와 조회 컬럼을 인덱스에서 읽음 |

실행계획 숫자 열은 이 실습의 실행 시간 측정값으로 해석하지 않는다. 버전이나 데이터에 따라 계획은 달라질 수 있다.

## 재현과 SQLite 문법

모든 시각은 한국 현지 시각으로 작성한 고정 샘플이다. 현재 시각 함수에 의존하지 않아
다른 날 실행해도 같은 결과가 나온다. 같은 ISO 형식의 TEXT는 문자열 비교로 기간을 조회할 수 있다.
금액은 원 단위 INTEGER로 저장해 부동소수점 금액 오차를 피한다.

MySQL에서는 가입일에 DATE, 주문시각에 DATETIME을, PostgreSQL에서는 DATE와 TIMESTAMP를
선택할 수 있다. SQLite는 전용 날짜 저장 타입 대신 TEXT 등으로 표현하므로 이 과제에서는
형식을 고정한 ISO 문자열을 사용한다. 다른 DB로 옮길 때 날짜 타입과 함수를 함께 조정한다.

SQLite 설정 `PRAGMA`, 실행 계획 `EXPLAIN QUERY PLAN`, 변경 행 수 `changes()`,
자료형 검사 `typeof()`, 월 추출 `substr()` 사용 위치에 주석을 달았다.
`LIMIT`도 사용하는 DB에 따라 문법을 조정해야 한다.
DDL과 샘플 입력은 각각 트랜잭션으로 묶는다. Q14·Q15는 실행 순서에 따라 DB를 변경한다.
보너스 정정 INSERT는 트랜잭션 안에서 확인 후 ROLLBACK하므로 추가 데이터가 남지 않는다.
