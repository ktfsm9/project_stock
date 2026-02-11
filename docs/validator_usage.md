# validate_pipeline_log 사용법 (Bash / PowerShell)

`tools/validate_pipeline_log.py`는 경고가 있으면 기본적으로 종료코드 `2`를 반환합니다.

## Bash

```bash
python tools/validate_pipeline_log.py docs/sample_run.log --print-exit-code
echo $?
```

## PowerShell

`$?` 는 **성공/실패(Boolean)** 이므로 숫자 종료코드를 보려면 `$LASTEXITCODE`를 확인해야 합니다.

```powershell
python tools/validate_pipeline_log.py docs/sample_run.log --print-exit-code
$LASTEXITCODE
```

- `$?` 결과 예시: `False` (종료코드가 0이 아님)
- `$LASTEXITCODE` 결과 예시: `2`

## 옵션

- `--lenient`: 경고가 있어도 종료코드 `0` 반환 (리포트 모드)
- `--print-exit-code`: 출력 마지막에 `EXIT_CODE: <n>`를 명시
