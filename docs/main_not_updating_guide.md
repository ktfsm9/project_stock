# main 브랜치가 업데이트 안 될 때 체크 가이드

증상(스크린샷 기준):
- `main`은 기본 브랜치인데 최근 커밋이 작업 브랜치(`codex/...`)에만 있고
- PR은 열려 있지만 `main` 커밋이 그대로인 상태

핵심 원인:
1. **PR을 열기만 하고 Merge를 안 한 경우**
2. 작업 브랜치만 push되고 `main` 직접 push가 안 된 경우
3. 로컬에서 `main`으로 fast-forward를 안 한 경우

---

## GitHub에서 즉시 반영하는 가장 쉬운 방법

1. PR 페이지로 이동
2. `Merge pull request` 클릭
3. `Confirm merge` 클릭
4. Branches 화면 새로고침

> PR이 merge되어야 `main`이 업데이트됩니다.

---

## 로컬에서 `main`에 반영 후 push하는 방법

PowerShell/Bash 공통 개념:

```bash
git checkout main
git merge --ff-only <작업브랜치>
git push origin main
```

예시:

```bash
git checkout main
git merge --ff-only work
git push origin main
```

---

## 자동화 스크립트 사용

현재 브랜치를 `main`에 fast-forward하고, 필요 시 push:

```bash
bash tools/sync_main_branch.sh --source work --push
```

- `--push`를 빼면 로컬 `main`만 업데이트
- `origin`이 없으면 push는 건너뜀(경고 출력)

---

## PowerShell에서 상태 확인 팁

```powershell
git branch -vv
git log --oneline --decorate --graph -20
git remote -v
```

그리고 GitHub PR 상태에서
- `Merged` 여부
- base 브랜치가 `main`인지
를 꼭 확인하세요.


---

## WSL 없이 PowerShell에서 바로 실행

질문처럼 `bash` 실행 시 WSL 미설치 오류가 나면, 아래 방법 중 하나를 사용하세요.

### 방법 A) 이미 PowerShell 프롬프트 안에 있을 때 (가장 권장)

```powershell
.\tools\sync_main_branch.ps1 -Source work -Push
```

> 실행 정책 오류가 나면 1회 허용:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\sync_main_branch.ps1 -Source work -Push
```

### 방법 B) CMD/다른 셸에서 PowerShell 스크립트 호출

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '.\tools\sync_main_branch.ps1' -Source 'work' -Push"
```

### 방법 C) 배치 래퍼 사용(따옴표/인코딩 이슈 회피)

```cmd
tools\sync_main_branch.bat -Source work -Push
```

- `-Push`를 빼면 로컬 `main`만 갱신
- `-Source` 생략 시 현재 브랜치를 source로 사용



## `CommandNotFound`(스크립트 못 찾음) 오류 해결

질문에 나온 아래 오류는 대부분 **현재 위치(cwd)가 스크립트가 있는 repo 루트가 아닐 때** 발생합니다.

- `'.\tools\sync_main_branch.ps1' ... 인식되지 않습니다`
- `'tools\sync_main_branch.bat' ... 모듈을 로드할 수 없습니다`

### 1) 현재 위치 확인

```powershell
Get-Location
Get-ChildItem
```

`tools` 폴더가 안 보이면 한 단계 아래 repo로 이동하세요(예: `cd .\project_stock`).

### 2) PowerShell에서는 경로 앞에 `./` 또는 `.\` 필수

```powershell
.\tools\sync_main_branch.bat -Source work -Push
```

> `tools\...`만 입력하면 PowerShell이 모듈 이름으로 해석할 수 있습니다.

### 3) 루트 래퍼(신규) 사용 — 가장 간단

repo 루트에서 아래처럼 실행하면 내부적으로 `tools/sync_main_branch.ps1`를 호출합니다.

```powershell
.\sync_main.ps1 -Source work -Push
```

또는

```cmd
.\sync_main.bat -Source work -Push
```
