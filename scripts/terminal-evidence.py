"""Run the submitted SQL in the real sqlite3 CLI, pausing for terminal screenshots.

No stored result text is read. The child sqlite3 process writes directly to this
terminal's stdout/stderr. PNG capture is a separate OS window-capture operation.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import sections  # Parse numbered SQL sections only; do not read result logs.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sqlite', type=Path, help='Official sqlite3 executable')
    parser.add_argument('--control', type=Path, help='Optional file handshake for OS screenshot automation')
    args = parser.parse_args()
    sqlite = args.sqlite.resolve(strict=True)
    control = args.control.resolve() if args.control else None
    if control:
        if control.exists() and any(control.iterdir()):
            raise RuntimeError('Use a new empty control directory for each capture session')
        control.mkdir(parents=True, exist_ok=True)
    version = subprocess.check_output([str(sqlite), '-version'], text=True).strip()
    sources = ['sql/03_queries.sql', 'bonus/01_join_subquery.sql',
               'bonus/02_integrity.sql', 'bonus/03_report.sql', 'bonus/04_evidence.sql']
    evidence = []
    # Only this newly created temporary directory is cleaned on exit.
    with tempfile.TemporaryDirectory(prefix='b6-1-sqlite-terminal-') as directory:
        temporary = Path(directory).resolve()
        assert temporary.parent == Path(tempfile.gettempdir()).resolve()
        for database in ('core.db', 'bonus.db'):
            script = '\n'.join((ROOT / 'sql' / name).read_text(encoding='utf-8')
                               for name in ('01_schema.sql', '02_seed.sql'))
            subprocess.run([str(sqlite), '-batch', database], cwd=temporary,
                           input=script.encode('utf-8'), check=True)
        for source in sources:
            for number, title, sql in sections(ROOT / source):
                if number is None:
                    continue
                name = number.lower()
                database = 'core.db' if number.startswith('Q') else 'bonus.db'
                filename = name + '.sql'
                script = '.nullvalue NULL\n.explain off\nPRAGMA foreign_keys = ON;\n' + sql.strip() + '\n'
                (temporary / filename).write_text(script, encoding='utf-8')
                # Clear the actual terminal viewport before this execution.
                print('\033[2J\033[H', end='', flush=True)
                print(f'B6-1 | {number} | Native SQLite CLI execution', flush=True)
                print(title, flush=True)
                print(f'Source: {source} | database: {database}', flush=True)
                print('SQLite ' + version.split()[0], flush=True)
                command = [str(sqlite), '-batch', '-echo', '-header', '-column', database, '.read ' + filename]
                print(f'COMMAND: sqlite3 -batch -echo -header -column {database} ".read {filename}"\n', flush=True)
                # stdout/stderr are inherited: sqlite3.exe itself writes to the terminal.
                completed = subprocess.run(command, cwd=temporary)
                expected_error = re.search(r'^-- EXPECT_ERROR: (.+)$', sql, re.MULTILINE)
                expected_code = 1 if expected_error else 0
                if completed.returncode != expected_code:
                    raise RuntimeError(f'{number}: unexpected exit code {completed.returncode}')
                print(f'\n[sqlite3 exit code: {completed.returncode}'
                      + ('; deliberate constraint error' if expected_error else '') + ']', flush=True)
                print('[Execution finished. Capture this terminal window before continuing.]', flush=True)
                entry = {'id': number, 'source': source,
                         'section_sha256_lf': hashlib.sha256(sql.encode('utf-8')).hexdigest(),
                         'cli_input_sha256': hashlib.sha256(script.encode('utf-8')).hexdigest(),
                         'cli_input': script, 'database': database,
                         'exit_code': completed.returncode, 'expected_error': expected_error.group(1) if expected_error else None}
                evidence.append(entry)
                if control:
                    ready = control / 'ready.json'
                    temp_ready = control / 'ready.tmp'
                    temp_ready.write_text(json.dumps({'id': number, 'sqlite_version': version,
                                                      'records': evidence}, ensure_ascii=False, indent=2), encoding='utf-8')
                    temp_ready.replace(ready)
                    advance = control / (name + '.next')
                    while not advance.exists():
                        time.sleep(0.15)
                    advance.unlink()
                else:
                    input('Press Enter for the next execution: ')
        # Confirm final tables in the exact DB used by the native CLI screenshots.
        query = "SELECT 'customer',COUNT(*) FROM customer UNION ALL SELECT 'menu',COUNT(*) FROM menu UNION ALL SELECT 'cafe_order',COUNT(*) FROM cafe_order UNION ALL SELECT 'order_item',COUNT(*) FROM order_item;"
        counts = subprocess.check_output([str(sqlite), '-batch', 'core.db', query], cwd=temporary, text=True).strip()
        assert counts.splitlines() == ['customer|11','menu|12','cafe_order|16','order_item|32'], counts
        if control:
            (control / 'completed.json').write_text(json.dumps({'sqlite_version':version, 'records':evidence,
                'final_counts': counts.splitlines()}, ensure_ascii=False, indent=2), encoding='utf-8')
        print('\nCompleted: 29 actual CLI executions; final row counts verified.', flush=True)
        if not control:
            input('Press Enter to close: ')


if __name__ == '__main__':
    main()
