# 세션 교체 핸드오프

컨텍스트 사용량 70% 도달 시 아래 절차로 세션을 교체합니다.

## 현재 상태 파악 명령

```bash
git status && git log --oneline -5
python3 -m unittest discover -s tests -v
```

## 다음 세션 시작 프롬프트 템플릿

---
**저장소:** watchcat — 한글 파일명 NFD→NFC 교정 Flet 앱
**현재 브랜치:** `<branch>`
**마지막 커밋:** `<hash> <message>`

**완료된 작업:**
- [ ] (항목 기입)

**남은 작업:**
- [ ] (항목 기입)

**주의 사항:** CI는 flet-cli 0.83.1 고정. Flutter override 제거 금지. 상세 → `AGENTS.md`

**다음 할 일:** (구체적 지시 기입)

---

## 세션 교체 판단 기준

- 컨텍스트 70% 초과
- 작업 단위 경계 (기능 완료, PR 생성 후)
- 에러 반복 3회 이상 → 새 세션에서 재시도
