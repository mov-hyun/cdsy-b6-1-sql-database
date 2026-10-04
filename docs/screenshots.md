# 실행 결과 캡처 안내

[전체 스크린샷](../results/screenshots/README.md)은 총 29장이다.
Q01~Q15 핵심 쿼리, Q16 인덱스, B01~B04 보너스 실험, M01~M03 리포트,
E01~E06 추가 검증을 각각 하나의 PNG로 제공한다.

## 캡처 대상과 출처

`run.py`로 SQLite SQL을 실제로 실행한 뒤 생성된 `results/*.txt`를 문서 화면으로 표시했다.
Playwright로 Microsoft Edge의 전체 페이지를 캡처했으며, SQL과 결과값을 직접 입력하거나 변경하지 않았다.
이는 실행 로그를 보여주는 문서의 브라우저 캡처다. DBeaver 등 DB 관리 도구의 UI 캡처와는 구분된다.
서비스 화면이나 백엔드 API는 구현하지 않았다. HTML은 제출 근거를 읽기 좋게 표시하는 중간 문서다.

이미지에는 쿼리 번호, 설명, 실행 SQL, 실제 결과, Python·SQLite 버전, 원본 파일명과 SHA-256을 표시한다.
해시는 Windows/Linux 줄바꿈 차이를 제거한 LF 정규화 텍스트 기준이다.
[manifest.json](../results/screenshots/manifest.json)에서 이미지와 원본을 일대일로 확인할 수 있다.

## 이미지 재생성

일반 SQL 재실행에는 기존처럼 Python만 있으면 된다. 이미지 재생성에만 Node.js, Playwright,
Microsoft Edge가 필요하다. 이 의존성이 준비된 환경에서 실행한다.

```powershell
node scripts/capture-results.cjs python
```

현재 Codex 번들 환경에서는 다음처럼 실행할 수 있다. 아래 변수는 현재 PowerShell 세션에서만 설정된다.

```powershell
$env:NODE_PATH = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
$capturePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
node scripts/capture-results.cjs $capturePython
```

이 명령은 먼저 SQL 전체와 검증을 재실행하므로 `data/cafe.db`와 텍스트 결과도 새로 생성한다.
검증에 실패하면 캡처를 진행하지 않는다. 실행 로그의 컬럼은 표로, 단일 컬럼·오류 메시지는 텍스트로 표시한다.
중간 HTML/PNG는 `output/playwright/sql-captures/`에, 제출용 PNG는 `results/screenshots/`에 저장한다.
캡처는 전체 페이지를 포함하며 가로 넘침이 발견되면 오류로 종료한다.
SQL이나 결과를 수정하면 위 명령으로 이미지도 함께 갱신해야 한다.
