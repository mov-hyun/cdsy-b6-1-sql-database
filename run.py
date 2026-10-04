"""SQLite 과제 SQL을 실행하고 실제 결과를 저장한다. Python 표준 라이브러리만 사용."""

from pathlib import Path
import re
import sqlite3
import sys


ROOT = Path(__file__).resolve().parent
TABLES = ('customer', 'menu', 'cafe_order', 'order_item')


def seeded_connection():
    connection = sqlite3.connect(':memory:', isolation_level=None)
    for filename in ('01_schema.sql', '02_seed.sql'):
        connection.executescript((ROOT / 'sql' / filename).read_text(encoding='utf-8'))
    return connection


def statements(sql):
    """각 SQL 문은 줄 끝에서 끝난다. complete_statement로 주석/문자열을 구별한다."""
    pending = ''
    for line in sql.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            yield pending.strip()
            pending = ''
    if any(line.strip() and not line.lstrip().startswith('--')
           for line in pending.splitlines()):
        raise ValueError('세미콜론으로 끝나지 않은 SQL이 있습니다.')


def sections(path):
    content = path.read_text(encoding='utf-8')
    markers = list(re.finditer(r'^-- ([QBM]\d{2}) \| (.+)$', content, re.MULTILINE))
    if not markers:
        raise ValueError(f'{path.name}: 쿼리 번호가 없습니다.')
    yield None, '', content[:markers[0].start()]
    for position, marker in enumerate(markers):
        end = markers[position + 1].start() if position + 1 < len(markers) else len(content)
        yield marker.group(1), marker.group(2), content[marker.end():end]


def run_file(connection, path, logs):
    """쿼리별 SQL/컬럼/행/변경 수를 기록하며 예상하지 못한 오류는 즉시 중단한다."""
    results = {}
    for number, title, sql in sections(path):
        if number is None:
            for statement in statements(sql):
                connection.execute(statement)
            continue
        output = [f'{number} | {title}', f'Source: {path.relative_to(ROOT).as_posix()}', '']
        rowsets = []
        expected = re.search(r'^-- EXPECT_ERROR: (.+)$', sql, re.MULTILINE)
        error_seen = False
        for statement in statements(sql):
            output.extend(['SQL:', statement, 'RESULT:'])
            try:
                cursor = connection.execute(statement)
            except sqlite3.IntegrityError as error:
                if expected is None or str(error) != expected.group(1):
                    raise
                error_seen = True
                output.extend([f'EXPECTED ERROR: {error}', ''])
                continue
            if cursor.description:
                rows = cursor.fetchall()
                rowsets.append(rows)
                output.append('\t'.join(column[0] for column in cursor.description))
                output.extend('\t'.join('NULL' if value is None else str(value) for value in row)
                              for row in rows)
                output.append(f'({len(rows)} rows)')
            elif cursor.rowcount >= 0:
                output.append(f'({cursor.rowcount} rows affected)')
            else:
                output.append('OK')
            output.append('')
        if expected is not None and not error_seen:
            raise AssertionError(f'{number}: 예상한 무결성 오류가 발생하지 않았습니다.')
        logs[f'{number.lower()}.txt'] = '\n'.join(output).rstrip('\n') + '\n'
        results[number] = rowsets
    return results


def require(condition, message, checks):
    if not condition:
        raise AssertionError(message)
    checks.append(f'PASS | {message}')


def verify_seed(connection, checks):
    require(connection.execute('PRAGMA foreign_keys').fetchone() == (1,),
            '외래키 검사 활성화', checks)
    counts = tuple(connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                   for table in TABLES)
    require(counts == (12, 12, 16, 32), f'초기 행 수 customer/menu/cafe_order/order_item = {counts}', checks)
    for table in TABLES:
        require(any(column[5] for column in connection.execute(f'PRAGMA table_info({table})')),
                f'{table}: PK 존재', checks)
    foreign_keys = sum(len(connection.execute(f'PRAGMA foreign_key_list({table})').fetchall())
                       for table in TABLES)
    require(foreign_keys == 3, '3개 FK로 1:N 관계 구성', checks)
    require(connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type IN ('view','trigger')").fetchone() == (0,),
            '뷰 및 트리거 미사용', checks)
    invalid_cases = [
        ('없는 고객 FK', "INSERT INTO cafe_order VALUES (99, 999, '2026-10-04 12:00:00', 'placed')", 'FOREIGN KEY'),
        ('없는 주문 FK', 'INSERT INTO order_item VALUES (99, 999, 1, 1, 3000)', 'FOREIGN KEY'),
        ('없는 메뉴 FK', 'INSERT INTO order_item VALUES (99, 1, 999, 1, 3000)', 'FOREIGN KEY'),
        ('참조 중인 고객 삭제', 'DELETE FROM customer WHERE customer_id = 1', 'FOREIGN KEY'),
        ('참조 중인 주문 삭제', 'DELETE FROM cafe_order WHERE order_id = 1', 'FOREIGN KEY'),
        ('참조 중인 메뉴 삭제', 'DELETE FROM menu WHERE menu_id = 1', 'FOREIGN KEY'),
        ('중복 PK', "INSERT INTO customer VALUES (1, '중복', 'new@example.com', '2026-10-04')", 'UNIQUE'),
        ('중복 이메일 UNIQUE', "INSERT INTO customer VALUES (99, '중복', 'customer01@example.com', '2026-10-04')", 'UNIQUE'),
        ('이름 NOT NULL', 'UPDATE customer SET name = NULL WHERE customer_id = 1', 'NOT NULL'),
        ('0 수량 CHECK', 'UPDATE order_item SET quantity = 0 WHERE order_item_id = 1', 'CHECK'),
        ('소수 수량 CHECK', 'UPDATE order_item SET quantity = 1.5 WHERE order_item_id = 1', 'CHECK'),
        ('음수 가격 CHECK', 'UPDATE menu SET price = -1 WHERE menu_id = 1', 'CHECK'),
        ('잘못된 상태 CHECK', "UPDATE cafe_order SET status = 'unknown' WHERE order_id = 1", 'CHECK'),
        ('주문 내 동일 메뉴 UNIQUE', 'INSERT INTO order_item VALUES (99, 1, 1, 1, 3000)', 'UNIQUE'),
    ]
    for title, sql, expected in invalid_cases:
        connection.execute('SAVEPOINT invalid_case')
        try:
            connection.execute(sql)
        except sqlite3.IntegrityError as error:
            require(expected in str(error), f'{title} 차단: {error}', checks)
        else:
            raise AssertionError(f'{title}: 잘못된 데이터가 허용되었습니다.')
        finally:
            connection.execute('ROLLBACK TO invalid_case')
            connection.execute('RELEASE invalid_case')


def main():
    logs = {}
    checks = []
    connection = seeded_connection()
    bonus_connection = seeded_connection()
    try:
        verify_seed(connection, checks)
        core = run_file(connection, ROOT / 'sql' / '03_queries.sql', logs)
        require(list(core) == [f'Q{number:02}' for number in range(1, 17)], 'Q01~Q16 전체 실행', checks)
        require(core['Q07'][0] == [(11, '고객11'), (12, '삭제실습고객')], 'LEFT JOIN: 주문 없는 고객 11, 12', checks)
        require(core['Q09'][0][0] == (1, '고객01', 3), '고객01 완료 주문 3건, 상세 수로 중복 집계하지 않음', checks)
        require([row[0] for row in core['Q09'][0] if row[2] == 0] == [4, 11, 12],
                '완료 주문 없는 고객 3명도 0건으로 유지', checks)
        require(core['Q11'][0][0] == (1, '고객01', 3, 10166.67), '평균 주문 금액은 고객01의 30,500 / 3 = 10,166.67원', checks)
        require(core['Q13'][0] == [(11, '딸기스무디'), (12, '캐모마일')], '미판매 메뉴 11, 12', checks)
        require(core['Q14'][1] == [(1,)] and core['Q14'][2][0][2] == 3200,
                'UPDATE 1행, 현재 가격 3,200원', checks)
        require(all(row[2] == 3000 for row in core['Q14'][3]), '과거 아메리카노 주문 단가 3,000원 보존', checks)
        require(core['Q15'][1] == [(1,)] and core['Q15'][2] == [] and core['Q15'][3] == [(11,)],
                'DELETE 1행, 삭제 대상 없음, 고객 11행 유지', checks)
        require(connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_cafe_order_customer_time'").fetchone() == (1,),
                '고객/주문시간 복합 인덱스 생성', checks)

        bonus = {}
        for filename in ('01_join_subquery.sql', '02_integrity.sql', '03_report.sql'):
            bonus.update(run_file(bonus_connection, ROOT / 'bonus' / filename, logs))
        require(bonus['B01'][0] == bonus['B02'][0] and len(bonus['B01'][0]) == 9,
                'JOIN과 EXISTS 결과 동일: 구매 고객 9명', checks)
        require(bonus['B04'][-1] == [(0,)], '정정 INSERT 성공 후 실습 주문 롤백', checks)
        require(bonus['M01'][0] == [('2026-09', 9, 104800), ('2026-10', 4, 51500)],
                '월별 주문/매출: 9월 9건 104,800원, 10월 4건 51,500원', checks)
        require(bonus['M02'][0][0] == (8, '버터크루아상', 8, 28000), '판매량 1위 크루아상 8개, 28,000원', checks)
        require(bonus['M03'][0] == [(9, 3, 33.33)], '반복 구매 고객 비율 3 / 9 = 33.33%', checks)
        bonus_connection.execute('BEGIN')
        bonus_connection.execute("UPDATE cafe_order SET status = 'cancelled'")
        empty_report = run_file(bonus_connection, ROOT / 'bonus' / '03_report.sql', {})
        require(empty_report['M01'][0] == [] and empty_report['M02'][0] == []
                and empty_report['M03'][0] == [(0, 0, None)],
                '완료 주문 0건: 매출/랭킹 빈 결과, 구매자 0명, 비율 NULL', checks)
        bonus_connection.execute('ROLLBACK')

        final_counts = tuple(connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                             for table in TABLES)
        require(final_counts == (11, 12, 16, 32), f'변경 후 모든 테이블 10행 이상: {final_counts}', checks)
        require(connection.execute('PRAGMA foreign_key_check').fetchall() == [], '최종 FK 위반 0건', checks)
        require(connection.execute('PRAGMA integrity_check').fetchall() == [('ok',)], '최종 DB integrity_check = ok', checks)
        # 쿼리 번호 주석과 무관하게 전체 SQL 파일 자체도 일반 도구에서 실행 가능해야 한다.
        plain = seeded_connection()
        try:
            plain.executescript((ROOT / 'sql' / '03_queries.sql').read_text(encoding='utf-8'))
            require('\n'.join(plain.iterdump()) == '\n'.join(connection.iterdump()),
                    '핵심 SQL 파일 전체 실행과 결과 수집 실행의 최종 DB 동일', checks)
        finally:
            plain.close()

        (ROOT / 'data').mkdir(exist_ok=True)
        with sqlite3.connect(ROOT / 'data' / 'cafe.db') as destination:
            connection.backup(destination)
        destination.close()
        logs['00_environment.txt'] = (
            f'Python {sys.version.split()[0]}\nSQLite {sqlite3.sqlite_version}\n'
            'Engine: Python standard-library sqlite3 (local SQLite)\n'
            'Foreign keys: ON on every execution connection\n'
            'Core: fresh schema -> seed -> Q01 through Q16\n'
            'Bonus: separate fresh schema -> seed -> B01 through B04 -> M01 through M03\n'
            'Money: integer KRW; sample dates: 2026-09-01 through 2026-10-04\n'
            f'Initial row counts: {dict(zip(TABLES, (12, 12, 16, 32)))}\n'
            f'Final row counts: {dict(zip(TABLES, final_counts))}\n'
        )
        logs['verification.txt'] = '\n'.join(checks) + f'\n\n{len(checks)} checks passed.\n'
        (ROOT / 'results').mkdir(exist_ok=True)
        for filename, content in logs.items():
            (ROOT / 'results' / filename).write_text(content, encoding='utf-8')
        print(f'PASS: {len(checks)} checks; 16 core/index sections; 7 bonus sections.')
        print('Saved data/cafe.db and results/*.txt')
    finally:
        connection.close()
        bonus_connection.close()


if __name__ == '__main__':
    main()
