# 난관과 해결 과정

이 문서는 실제 작업에서 발생한 실행 문제와 의도적으로 수행한 SQL 실패 실습을 구분해 기록한다.
개인의 감상이나 경험을 대신 작성하지 않고, 관찰된 증상·원인·조치·확인 결과를 정리했다.

## 1. Python과 SQLite 실행 명령을 찾을 수 없었던 문제

**실제 발생한 환경 문제.** 초기 PowerShell에서 다음 명령으로 도구를 찾았지만 결과가 없었다.

```powershell
Get-Command python,py,sqlite3 -ErrorAction SilentlyContinue
```

원인은 실행 파일이 PATH에서 발견되지 않는 것이었다. 설치 유무를 PATH 검색 결과만으로 단정하지 않고,
작업 환경에 제공된 번들 Python을 확인했다. 해당 Python의 표준 sqlite3 모듈로 로컬 DB 실행이 가능했다.

해결 순서:

1. 번들 Python으로 Python·SQLite 버전을 확인했다.
2. `run.ps1`에서 번들 Python을 먼저 찾고 일반 python/py 명령을 대안으로 사용하도록 했다.
3. 다음 명령으로 스키마·샘플·쿼리·검증 전체를 실행했다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

현재 보완본의 실제 성공 출력:

```text
PASS: 47 checks; 16 core/index sections; 13 bonus/evidence sections.
Saved data/cafe.db and results/*.txt
```

확인 자료: [환경 버전](../results/00_environment.txt), [검증 기록](../results/verification.txt),
[실행 스크립트](../run.ps1). 새 DB 연결에서는 `PRAGMA foreign_keys = ON`을 다시 설정한다.

## 2. 없는 고객으로 주문을 입력했을 때 FK 오류가 발생하는 이유

**의도적인 무결성 실패 실습.** 고객 999를 참조하는 주문을 입력했다.

```sql
PRAGMA foreign_keys = ON;
INSERT INTO cafe_order (order_id, customer_id, ordered_at, status)
VALUES (99, 999, '2026-10-04 12:00:00', 'placed');
```

실제 결과는 `FOREIGN KEY constraint failed`였다. customer에 999가 없으므로 주문이 부모를 참조할 수 없다.

해결 순서:

1. 참조 대상 고객이 존재하는지 확인한다. 샘플의 customer_id=1은 존재한다.
2. customer_id를 1로 수정해 트랜잭션 안에서 같은 주문 99를 입력한다.
3. SELECT로 `(99, 1, placed)`를 확인하고 ROLLBACK한다. 복구 후 주문 99는 0건이다.

실제 신규 고객의 주문이라면 먼저 고객을 INSERT해야 한다. 오류를 피하려고 FK 검사를 끄지 않는다.
전체 재현 SQL: [bonus/02_integrity.sql](../bonus/02_integrity.sql).
증거: [실패 텍스트](../results/b03.txt), [실패 이미지](../results/screenshots/b03.png),
[정정·복구 텍스트](../results/b04.txt), [정정·복구 이미지](../results/screenshots/b04.png).

추가로 고객 1을 삭제하면 남아 있는 주문 때문에 RESTRICT가 차단한다.
이는 데이터를 고아 상태로 만들지 않도록 의도한 동작이다. Q15에서는 주문 없는 실습 고객 12를 삭제한다.
증거: [부모 삭제 실패](../results/e02.txt), [조건을 충족한 삭제](../results/q15.txt).

## 3. 실행 결과 파일 끝에 불필요한 빈 줄이 생긴 문제

**실제 발생한 제출 파일 문제.** 첫 커밋 전 `git diff --cached --check`에서
`results/q01.txt:17: new blank line at EOF.` 등 결과 파일의 빈 줄 경고가 발생했다.

결과 구간 사이에 빈 줄을 넣는 출력 목록의 마지막 항목도 빈 문자열인데,
파일 저장 시 줄바꿈을 한 번 더 붙여 마지막에 빈 줄이 남는 것이 원인이었다.

해결 순서:

1. `run_file()`의 저장 문자열을 `'\n'.join(output).rstrip('\n') + '\n'`로 수정했다.
2. SQL을 재실행해 결과 파일을 모두 다시 생성했다.
3. 다시 스테이징하고 `git diff --cached --check`에서 오류가 없음을 확인한 뒤 최초 커밋했다.

SQL과 결과값은 유지하고 파일 끝의 줄바꿈만 한 번으로 정리했다.
현재 구현: [run.py](../run.py). 이 항목은 최초 커밋 전 실제 작업 기록이며, 현재 스테이징 작업을 요구하지 않는다.

## 4. 설계 중 주의한 집계 문제

**예방적으로 검토한 논리 문제.** 주문과 상세를 연결하면 주문 한 건이 상세 수만큼 반복된다.
현재 샘플의 완료 주문 13건에는 상세 26행이 있으므로 조인 결과의 COUNT(*)를 주문 건수로 쓰면 잘못된다.
M01은 `COUNT(DISTINCT order_id)`로 세고, Q11은 주문별 금액을 먼저 만든 뒤 AVG를 계산한다.

이 항목은 실제 발생했다고 주장하는 장애 기록이 아니라 설계 검토 내용이다.
검증은 고객01의 3건·총 30,500원·평균 10,166.67원을 기대값으로 대조했다.
증거: [Q11](../results/q11.txt), [월별 집계 M01](../results/m01.txt), [검증 기록](../results/verification.txt).
