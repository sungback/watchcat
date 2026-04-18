# AGENTS.md

## 목적

이 파일은 이 저장소를 다루는 코딩 에이전트와 자동화를 위한 문서입니다.

## 완료 전 필수 확인 사항

1. 실행:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
2. 빌드 관련 파일이 바뀌었다면 확인:
   ```bash
   flet build macos --yes
   ```
3. 패키징이나 CI 동작을 바꿨다면 확인:
   - `build/flutter/app/app.zip`
   - `build/flutter/pubspec.yaml`

## 패키징 제약

- `main.py`는 Flet 엔트리포인트로 저장소 루트에 유지합니다.
- 앱 패키지 exclude 규칙은 의도된 설정이므로, 같은 수준으로 엄격한 대안이 없는 한 유지해야 합니다.
- 생성된 Flutter shell은 `pyproject.toml`의 `tool.flet.flutter.pubspec` override를 사용합니다.

## CI 제약

- CI는 의도적으로 `uvx --from "flet-cli==0.83.1"`로 Flet 빌드를 수행합니다.
- macOS 빌드는 의도적으로 `macos-15`를 사용합니다.
- macOS CI가 네이티브 컴파일에서 실패하면 Python 코드를 바꾸기 전에 플러그인 버전부터 확인해야 합니다.
- `build-desktop.yml`은 일반 push/PR에서 빌드 검증만 수행하며 artifact를 업로드하지 않습니다.
- GitHub Release 파일 생성은 `release-desktop.yml`의 `v*` 태그 push에서만 일어납니다.
- 공개 macOS 배포물은 반드시 `release-desktop.yml` 결과만 사용해야 합니다.

## 반드시 설명이 유지되어야 하는 의존성 override

현재 CI 안정성을 위해 아래 설정이 존재합니다.

```toml
[tool.flet.flutter.pubspec.dependency_overrides]
connectivity_plus = "7.0.0"
device_info_plus = "12.3.0"
```

이유:

- Flutter 플러그인 해상도를 고정하지 않으면 `connectivity_plus 7.1.1`이 선택되었습니다.
- 해당 버전은 CI에서 아래 오류로 실패했습니다.
  `NWPath has no member 'isUltraConstrained'`

## 기능 불변 조건

- 정규화 과정에서 이미 존재하는 다른 파일을 조용히 덮어쓰면 안 됩니다.
- rename 연속 작업이 실패하면 롤백해야 합니다.
- Bulk fix는 부모보다 자식을 먼저 처리해야 합니다.
- 실시간 감시와 bulk fix는 같은 핵심 rename 로직을 공유해야 합니다.
- 최종 macOS 릴리스 검증은 staging `.app`만이 아니라, 패키징된 zip을 다시 풀어 검사하는 단계까지 포함해야 합니다.
