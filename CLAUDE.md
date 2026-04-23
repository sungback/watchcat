# CLAUDE.md

## 프로젝트 개요

watchcat은 한글 파일명 정규화 문제를 교정하는 Flet 데스크톱 애플리케이션입니다.
루트 `main.py` 엔트리포인트는 Flet 패키징 의존성 때문에 유지합니다.

## 코드 구조

- `main.py`: Flet용 import-only 엔트리포인트
- `watchcat_app/ui.py`: UI 구성과 monitor lifecycle
- `watchcat_app/path_fixer.py`: 정규화, 충돌 검사, 롤백 로직
- `watchcat_app/monitor.py`: `watchdog` 연동
- `watchcat_app/picker.py`: macOS 네이티브 폴더 선택기
- `watchcat_app/unicode_utils.py`: 로그용 자모 가시화
- `watchcat_app/platform.py`: `IS_MACOS`, `IS_WINDOWS` 플랫폼 상수

## 핵심 규칙

1. `tool.flet.app.module`/`path`를 함께 수정하지 않는 한 앱 시작점을 `main.py` 밖으로 옮기지 마십시오.
2. `pyproject.toml`의 app/package exclude 설정은 `app.zip` 내 잡파일 유입 확인 전까지 제거하지 마십시오.

> CI·배포·Flutter 의존성 관련 변경 시 → `AGENTS.md` 참조
> 빌드 명령 상세 → `docs/build.md` 참조
> 과거 장애·수정 이력 → `docs/incident-log.md` 참조

## 테스트

```bash
python3 -m unittest discover -s tests -v
```

커버: NFD→NFC rename, no-op, 충돌 skip, 롤백, bulk-fix 집계

## 빌드 (로컬)

```bash
flet build macos --yes
```

CI 빌드 상세 → `docs/build.md`
