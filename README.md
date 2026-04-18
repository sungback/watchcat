# watchcat

watchcat은 한글 파일명 정규화 문제를 교정하는 Flet 데스크톱 앱입니다.
주로 macOS에서 만들어진 분해형 NFD 파일명을 NFC로 바꾸는 용도입니다.

## 구조

- `main.py`: `flet build`를 위해 저장소 루트에 유지하는 얇은 Flet 엔트리포인트
- `watchcat_app/ui.py`: Flet UI와 감시/일괄 수정 연결
- `watchcat_app/path_fixer.py`: 파일명 정규화와 일괄 순회 로직
- `watchcat_app/monitor.py`: `watchdog` 이벤트 핸들러
- `watchcat_app/unicode_utils.py`: 로그 출력용 자모 가시화 유틸리티
- `tests/test_main.py`: 순수 정규화 동작에 대한 회귀 테스트

## 로컬 개발

`uv`로 의존성을 설치하고 테스트를 실행합니다.

```bash
uv sync
python3 -m unittest discover -s tests -v
```

로컬 빌드:

```bash
flet build macos --yes
```

## 빌드 관련 중요 사항

- `tool.flet.app.module`도 함께 바꾸지 않는 한 `main.py`는 루트 엔트리포인트로 유지해야 합니다.
- 앱 패키징 시 `pyproject.toml`을 통해 `tests`, `.venv`, `.claude`, `.git` 및 일반적인 캐시 디렉터리를 제외합니다.
- Flutter 의존성 드리프트 때문에 CI에서만 macOS 빌드가 깨진 적이 있습니다. 현재 저장소는 `pyproject.toml`의 `tool.flet.flutter.pubspec.dependency_overrides` 아래에서 다음 버전을 고정합니다.
  - `connectivity_plus = "7.0.0"`
  - `device_info_plus = "12.3.0"`
- CI도 `flet-cli==0.83.1`을 고정합니다. macOS 패키징 workflow를 다시 돌려보기 전에는 임의로 올리지 마십시오.

## CI 및 릴리스 규칙

- Desktop CI는 `uv run flet build ...` 대신 `uvx --from "flet-cli==${FLET_CLI_VERSION}" flet build ...`를 사용합니다.
- 현재 macOS CI는 디버깅 과정에서 더 최신 Flutter/플러그인 조합에 Xcode 16.x가 필요했기 때문에 `macos-15`를 대상으로 합니다.
- `build-desktop.yml`은 일반 push/PR에서 빌드 검증만 수행합니다. GitHub Release용 zip이나 Actions artifact를 만들지 않습니다.
- GitHub Release 업로드는 `release-desktop.yml`에서만 수행하며, `v*` 태그 push일 때만 실행됩니다.
- 공식 macOS 배포물은 반드시 `release-desktop.yml`이 만든 GitHub Release asset이어야 하며, 서명, notarization, stapling, zip 재검증까지 끝난 결과만 사용해야 합니다.
- 실패 진단 시 의도적으로 아래 경로를 덤프합니다.
  - `build/`
  - `build/flutter/build/`
  - `build/flutter/app/`

## 테스트로 보장하는 동작

- 없거나 이미 정규화된 경로는 건너뜁니다.
- NFD 이름은 올바르게 이름 변경되고 로그에도 반영됩니다.
- 이미 존재하는 정규화 대상 파일을 조용히 덮어쓰지 않습니다.
- 두 번째 단계 rename이 실패하면 원래 경로로 롤백합니다.
- bulk fix는 스캔 수와 수정 수를 정확히 집계합니다.

## 최근 주요 수정 사항

- Flet 패키징이 유지되도록 하면서 앱을 `watchcat_app/` 구조로 리팩터링했습니다.
- 정규화 과정에서 발생할 수 있는 덮어쓰기 충돌을 막았습니다.
- rename 연속 작업 실패 시 롤백을 추가했습니다.
- monitor 모드의 observer start/join 레이스를 제거했습니다.
- Flet CLI와 Flutter 플러그인 override 버전 고정으로 GitHub Actions macOS 빌드를 안정화했습니다.
