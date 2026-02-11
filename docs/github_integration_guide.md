# 로컬 저장소 ↔ GitHub 저장소 연동 가이드

요청하신 환경 기준:
- 로컬: `C:\stock_clean\project_stock`
- GitHub: `https://github.com/ktfsm9/project_stock`

아래 순서로 진행하면 됩니다.

## 1) 로컬 저장소로 이동

```powershell
cd C:\stock_clean\project_stock
```

## 2) Git 초기 상태 확인

```powershell
git status
git branch --show-current
git remote -v
```

`origin`이 없거나 URL이 다르면 3단계 진행.

## 3) origin 연결(또는 교체)

```powershell
git remote remove origin 2>$null
git remote add origin https://github.com/ktfsm9/project_stock.git
```

이미 `origin`이 있는데 URL만 바꾸려면:

```powershell
git remote set-url origin https://github.com/ktfsm9/project_stock.git
```

## 4) 기본 브랜치 정리(main 기준)

```powershell
git branch -M main
```

## 5) 최초 푸시 + 업스트림 설정

```powershell
git push -u origin main
```

## 6) 인증 이슈 발생 시

GitHub는 비밀번호 푸시를 허용하지 않으므로 아래 중 하나를 사용하세요.

- **GitHub CLI**
  ```powershell
  gh auth login
  ```
- **Personal Access Token (PAT)**
  - GitHub > Settings > Developer settings > Personal access tokens에서 생성
  - 푸시 시 비밀번호 대신 PAT 입력

## 자동화 스크립트(선택)

리눅스/WSL/맥 환경에서는 아래 스크립트로 한번에 설정 가능합니다.

```bash
bash tools/setup_github_remote.sh https://github.com/ktfsm9/project_stock.git main
```

## 체크 포인트

연동 완료 후 아래가 확인되면 정상입니다.

```powershell
git remote -v
git branch -vv
```

- `origin`이 `https://github.com/ktfsm9/project_stock.git`를 가리킴
- 현재 브랜치가 `origin/main`을 tracking


## main이 안 올라갈 때

작업 브랜치에서 PR만 열어두면 `main`은 자동으로 갱신되지 않습니다(merge 필요).

```bash
bash tools/sync_main_branch.sh --source work --push
```

또는 GitHub PR 화면에서 `Merge pull request`를 직접 수행하세요.
