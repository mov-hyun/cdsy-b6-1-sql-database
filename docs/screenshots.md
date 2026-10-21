# 실제 SQL 터미널 캡처 안내

[전체 캡처](../results/screenshots/README.md)는 Windows Terminal에서 독립 실행 파일
`sqlite3.exe`가 제출 SQL을 실행한 화면 29장이다. Q01~Q16, B01~B04, M01~M03, E01~E06을 포함한다.

## 이전 자료 정정

이전 이미지는 `results/*.txt`를 HTML로 표시한 브라우저 캡처였다. 실제 터미널에서 SQL을 실행하는
화면이라는 증거로 사용할 수 없으므로, 2026-10-21에 29장을 모두 교체하고 HTML 생성기를 삭제했다.
현재 PNG는 실제 Windows Terminal 창의 표시 영역을 OS 화면에서 직접 캡처한 파일이다.
일반 교체 커밋으로 수정했으므로 이전 이미지는 과거 Git 커밋에 남는다.

## 실행과 캡처 방식

1. `scripts/terminal-evidence.py`가 원본 스키마·시드로 임시 DB 두 개를 만든다.
   Q01~Q16은 `core.db`, 나머지는 별도로 초기화한 `bonus.db`에서 순서대로 실행한다.
2. 제출 SQL의 번호별 본문을 임시 SQL 파일로 옮긴 뒤 실제 `sqlite3.exe`를 호출한다.
   각 연결에 `PRAGMA foreign_keys = ON`을 적용하고, `-echo -header -column`으로 SQL과 결과를 표시한다.
   `.nullvalue NULL`은 NULL 표시를, `.explain off`는 실행계획의 표 형식을 설정하는 SQLite CLI 명령이다.
3. SQLite 프로세스가 표준 출력과 오류를 터미널에 직접 쓴다. Python은 실행 번호·설명·명령·종료 코드를 덧붙이고
   캡처까지 대기한다. 저장된 결과 텍스트나 HTML은 읽지 않는다.
4. `scripts/capture-terminal.py`가 제목이 일치하는 실제 터미널 창을 전면에 놓고,
   Pillow `ImageGrab`으로 화면에 표시된 창 영역을 캡처한다. 캡처 후 글자 합성·보정·재배치·리사이즈는 하지 않는다.
   다음 SQL 실행은 해당 화면 저장 이후에 진행한다.

제출 PNG는 창 제목 표시줄, 실행 SQL, 실제 출력, 종료 코드를 포함하며 크기는 2560×1380이다.
B03·E02·E03의 종료 코드 1은 의도적인 FK/PK 위반이다. 나머지 26개는 종료 코드 0이다.
오류 종류는 이미지에서 직접 확인할 수 있다. 자동 실행기는 종료 코드만 검사한다.
전체 실행 후 캡처에 사용한 핵심 DB의 행 수가 고객11·메뉴12·주문16·상세32임을 확인했다.

[manifest.json](../results/screenshots/manifest.json)에 실제 CLI 버전, 캡처 시각, PNG SHA-256,
원본 SQL 섹션의 LF 정규화 SHA-256, CLI에 전달한 SQL과 종료 코드를 기록했다.
해시는 파일 대응 및 변경 확인용이며 실행 자체에 대한 외부 인증은 아니다.

## 실행 환경과 텍스트 결과의 관계

- 이미지: Windows Terminal, 공식 Windows x64 SQLite CLI **3.54.1**, 화면 캡처용 Pillow **12.1.1**.
- 텍스트: Python **3.12.14** 표준 라이브러리 SQLite **3.53.1**. [환경 기록](../results/00_environment.txt) 참조.
- 두 경로는 동일한 제출 SQL과 샘플을 각각 실행한다. PNG는 텍스트 파일을 이미지로 변환한 자료가 아니다.
  엔진·출력 도구가 다르므로 공백, 표 정렬, 오류의 파일명·줄 번호, 실행계획의 내부 번호는 다를 수 있다.

실제 사용한 [공식 SQLite 도구 ZIP](https://www.sqlite.org/2026/sqlite-tools-win-x64-3540100.zip)의
SHA3-256은 아래와 같으며 다운로드 후 대조했다. 바이너리와 ZIP은 Git에 포함하지 않는다.

```text
e171f3993a992edf076746926dd52b5e2ebfabaee38818e74987e1d8112ab987
```

## 수동 재현

SQLite 공식 CLI와 Python을 준비한다. Windows Terminal에서 저장소 폴더로 이동한 뒤 실행한다.
아래 실행 파일 경로는 설치 위치에 맞게 바꾼다.

```powershell
python scripts/terminal-evidence.py C:\tools\sqlite3.exe
```

각 실행이 멈추면 SQL과 출력, 종료 코드가 모두 보이는 터미널 창을 캡처한다.
Enter를 누르면 다음 실습이 실행된다. 글자가 화면 밖으로 넘어가면 창 크기나 글꼴 크기를 조절해
전체 실행을 다시 캡처한다. 이 작업은 `data/cafe.db`나 기존 텍스트 결과를 덮어쓰지 않는다.

## 자동 캡처 재현

Windows와 Pillow가 필요하다(`python -m pip install Pillow`). 매번 **새 제어 폴더**를 사용한다.
첫 번째 터미널에서 저장소 폴더를 기준으로 다음처럼 새 창을 연다.

```powershell
wt -w new --maximized new-tab --title "B6-1 SQLite evidence" --suppressApplicationTitle -d . python scripts/terminal-evidence.py C:\tools\sqlite3.exe --control output/terminal-control-new
```

첫 SQL의 실행 완료 문구가 나타나면 다른 터미널에서 다음을 실행한다.

```powershell
python scripts/capture-terminal.py --control output/terminal-control-new
```

캡처 중에는 터미널 위에 다른 창을 띄우거나 화면을 조작하지 않는다. 실행기는 전면 창을 확인하지만
알림·팝업과 긴 출력의 잘림까지 자동 판정하지는 않으므로 저장된 이미지를 직접 확인한다.
29장 저장과 SQL 실행 완료 후 PNG 해시를 검사하고 목록과 manifest를 갱신한다.
이 명령은 제출용 PNG·목록·manifest를 덮어쓴다. 새 제어 폴더의 로그와 SQLite 실행 파일은 커밋하지 않는다.
