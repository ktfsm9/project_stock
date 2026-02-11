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
