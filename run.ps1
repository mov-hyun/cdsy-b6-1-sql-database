param([switch]$Console)
$ErrorActionPreference = 'Stop'

# Codex 번들 Python을 먼저 찾고, 없으면 일반 Python 설치를 사용한다.
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) {
    $pythonExecutable = $bundledPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExecutable = (Get-Command python).Source
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExecutable = (Get-Command py).Source
} else {
    throw 'Python 3.12 이상을 설치하고 다시 실행하세요. 외부 Python 패키지는 필요하지 않습니다.'
}

if ($Console) {
    $databasePath = Join-Path $PSScriptRoot 'data\cafe.db'
    if (-not (Test-Path -LiteralPath $databasePath)) {
        throw '먼저 run.ps1을 실행해 실습 DB를 생성하세요.'
    }
    & $pythonExecutable -m sqlite3 $databasePath
} else {
    & $pythonExecutable (Join-Path $PSScriptRoot 'run.py')
}
exit $LASTEXITCODE
