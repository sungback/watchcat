# CLAUDE.md

## 프로젝트 개요

watchcat은 한글 파일명 정규화 문제를 교정하는 Flet 데스크톱 애플리케이션입니다.
최근 저장소 구조를 패키지 기반으로 분리했지만, Flet 패키징이 여기에 의존하기 때문에
루트 `main.py` 엔트리포인트는 유지하고 있습니다.

## 코드 구조

- `main.py`: Flet용 import-only 엔트리포인트
- `watchcat_app/ui.py`: UI 구성과 monitor lifecycle
- `watchcat_app/path_fixer.py`: 정규화, 충돌 검사, 롤백 로직
- `watchcat_app/monitor.py`: `watchdog` 연동
- `watchcat_app/picker.py`: macOS 네이티브 폴더 선택기
- `watchcat_app/unicode_utils.py`: 로그용 자모 가시화

## 중요한 규칙

1. `tool.flet.app.module` 또는 `tool.flet.app.path`도 함께 수정하지 않는 한 앱 시작점을 루트 `main.py` 밖으로 옮기지 마십시오.
2. `build/flutter/app/app.zip`에 `.venv`, `.claude`, 테스트 파일 같은 저장소 내부 잡파일이 더 이상 들어가지 않는 것을 확인하기 전에는 `pyproject.toml`의 app/package exclude 설정을 제거하지 마십시오.
3. Flutter 의존성 override는 임의로 제거하지 마십시오.
   - `connectivity_plus = "7.0.0"`
   - `device_info_plus = "12.3.0"`
   이 설정은 upstream 플러그인 드리프트 때문에 발생한 CI 전용 macOS 네이티브 컴파일 실패를 막기 위해 추가했습니다.
4. CI의 `flet-cli` 버전은 임의로 올리지 마십시오. workflow는 `0.84.0`에서 `serious_python` macOS 패키징 회귀가 있었기 때문에 의도적으로 `0.83.1`을 고정합니다.
5. macOS CI가 다시 깨지면 앱 코드를 바꾸기 전에 생성된 `build/flutter/pubspec.yaml`부터 확인하십시오. 근본원인이 Python 코드가 아니라 Flutter 쪽 의존성 해상도일 수 있습니다.
6. 일반 `push`나 PR에서 도는 `build-desktop.yml`은 빌드 검증만 수행합니다. 공개
   배포는 `v*` 태그 push로 실행되는 `release-desktop.yml` 결과만 사용해야 합니다.

## 테스트 기준

실행:

```bash
python3 -m unittest discover -s tests -v
```

현재 회귀 테스트는 다음을 다룹니다.

- NFD에서 NFC로의 정상 rename
- no-op 케이스
- 충돌 시 skip 동작
- 두 번째 rename 실패 후 롤백
- bulk-fix의 스캔 수/수정 수 집계

## 빌드 기준

로컬 빌드 명령:

```bash
flet build macos --yes
```

CI 빌드 명령:

```bash
uvx --from "flet-cli==${FLET_CLI_VERSION}" flet build <target> --yes --verbose --clear-cache
```

## 최근 원인과 수정 사항

- `fix_path()`는 예전에 Unix 계열에서 이미 존재하는 정규화 대상 파일을 덮어쓸 수 있었습니다. 지금은 충돌을 감지하고 건너뜁니다.
- `fix_path()`는 두 번째 rename이 실패했을 때 임시 산출물을 남길 수 있었습니다. 지금은 롤백합니다.
- Monitor 모드는 예전에 `Observer.start()`를 별도 스레드로 한 번 더 감싸 `join before start` 레이스를 만들었습니다. 그 래퍼를 제거했습니다.
- CI는 한때 `serious_python` 패키징에서 실패했고, 이후에는 Flutter 플러그인 컴파일에서 실패했습니다. 현재의 안정적인 해결책은 다음 조합입니다.
  - workflow에서 `flet-cli` 버전 고정
  - macOS CI를 `macos-15`로 유지
  - `pyproject.toml`에서 Flutter 플러그인 override 버전 고정
- Gatekeeper 기준의 배포 검증은 staging `.app`만이 아니라 최종 패키징된 zip에서 해야 합니다. 실제 사용자는 릴리스 아카이브를 내려받아 열기 때문입니다.
- 일반 push에서는 GitHub Release 파일이 생성되지 않습니다. 릴리스 파일은 태그 push에서만 생성됩니다.
