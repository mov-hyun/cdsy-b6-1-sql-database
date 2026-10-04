# 사전평가 15개 항목별 보완 근거

사용자가 전달한 사전평가 이력은 다음과 같다.

| 평가 시각 | 결과 | FAIL 항목 |
|---|---|---|
| 2026-10-04 19:06:38 | 13/15 통과(87%) | #5 실행 스크린샷, #15 난관·해결 기록 |
| 2026-10-05 02:24:16 | 14/15 통과(93%) | #10 DB vs 엑셀 비교 |

2차 평가에서 지적한 비교 설명은 기존 [docs/design.md](design.md#엑셀과-관계형-db)에 포함되어 있다.
확인 경로를 줄이기 위해 [README 상단의 DB vs 엑셀](../README.md#db-vs-엑셀)에
관계 저장·참조 무결성·중복 관리·입력 제약·부모 삭제 비교 본문과 실제 오류 로그 링크를 직접 배치했다.
아래는 현재 보완본의 근거이며, README 상단 보완 이후의 재평가 결과는 아직 확인하지 않았다.

| 항목 | 확인할 내용 | 제출 근거 |
|---|---|---|
| #1 PK | 네 PK의 역할·수동 ID 전략을 컬럼 위 주석에 명시 | [스키마](../sql/01_schema.sql), [설계 설명](design.md) |
| #2 FK·1:N | 없는 부모 입력 및 참조 중인 부모 삭제 실패 | [B03 로그](../results/b03.txt), [B03 PNG](../results/screenshots/b03.png), [E02 PNG](../results/screenshots/e02.png) |
| #3 데이터 행 수 | customer 12, menu 12, cafe_order 16, order_item 32 | [COUNT SQL](../bonus/04_evidence.sql), [E01 로그](../results/e01.txt), [E01 PNG](../results/screenshots/e01.png) |
| #4 쿼리 종류 | 기본4·조인4·집계3·서브쿼리2·수정1·삭제1 + 인덱스1 | [README 쿼리 구성과 실행 증거](../README.md#쿼리-구성과-실행-증거) |
| #5 실행 스크린샷 | Q01~Q16 전부 PNG 첨부, 원본 텍스트와 대응 | [스크린샷 전체 목록](../results/screenshots/README.md), [캡처 방식](screenshots.md) |
| #6 테이블 분리·정규화 | 1NF/2NF/3NF와 실제 테이블 분리 이유 연결 | [설계 설명](design.md#왜-네-테이블로-나누었나) |
| #7 관계 시나리오 | 고객→주문, 주문→상세, 메뉴→상세의 생성·수정·삭제 예시 | [키와 제약조건](design.md#키와-제약조건) |
| #8 타입 | SQLite TEXT 날짜와 DATE/DATETIME/TIMESTAMP 비교 | [재현과 SQLite 문법](design.md#재현과-sqlite-문법) |
| #9 인덱스 | SCAN·임시 정렬 → COVERING INDEX SEARCH 비교 | [Q16 로그](../results/q16.txt), [Q16 PNG](../results/screenshots/q16.png), [해석](design.md#인덱스) |
| #10 DB·엑셀 | 관계 저장·무결성·중복·입력 제약·부모 삭제를 README 상단에서 직접 비교 | [README DB vs 엑셀 본문](../README.md#db-vs-엑셀), [상세 설명](design.md#엑셀과-관계형-db) |
| #11 PK·FK 동작 | PK 중복·없는 부모·부모 삭제 SQL과 실제 오류 | [SQL 예시](design.md#키와-제약조건), [E03 PNG](../results/screenshots/e03.png) |
| #12 JOIN | 같은 고객 1·11에 대해 INNER 3행 / LEFT 4행(NULL 포함) 비교 | [INNER PNG](../results/screenshots/e04.png), [LEFT PNG](../results/screenshots/e05.png) |
| #13 집계 경계 | COUNT·SUM·AVG의 NULL/0 처리, DISTINCT와 빈 입력 | [설명](design.md#sql을-어떻게-구분하나), [E06 로그](../results/e06.txt), [E06 PNG](../results/screenshots/e06.png) |
| #14 복잡 쿼리 | Q11을 완료 주문 필터 → 주문별 합계 → 고객별 평균의 3단계로 설명 | [단계별 설명](design.md#대표-복잡-쿼리-q11의-처리-순서), [Q11 PNG](../results/screenshots/q11.png) |
| #15 난관·해결 | 실제 PATH 문제·결과 파일 빈 줄 문제와 의도적 FK 실패 실습의 원인·해결·확인 | [난관과 해결 과정](troubleshooting.md) |

## 원문 요구사항과 사전평가의 차이

사용자가 제공한 과제 원문에는 결과 확인을 “스크린샷 또는 결과 텍스트”로 남길 수 있다고 되어 있다.
기존 제출물은 results/*.txt로 실행 결과를 제공했다. 이번 보완에서는 평가표 #5가 요청한 이미지도 추가했다.
README의 쿼리 유형 매핑, B03의 FK 실패 로그, Q16의 실행계획도 최초 제출물에 포함되어 있었으며,
이번에는 위 표에서 직접 연결해 확인 경로를 짧게 했다.

## 현재 검증

- [verification.txt](../results/verification.txt): 실제 실행 검증 47개 통과.
- 핵심·인덱스 16개, 보너스·보완 13개: SQL/실제 결과/PNG가 각각 대응.
- 이미지의 원본 텍스트 해시와 브라우저 버전: [manifest.json](../results/screenshots/manifest.json).
- 생성 DB는 `data/cafe.db`이며 기존 SQL 재실행으로 재현할 수 있다.
