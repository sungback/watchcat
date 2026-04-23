# AGENTS.md

## 완료 전 필수 확인 사항

1. `python3 -m unittest discover -s tests -v`
2. 빌드 관련 파일 변경 시: `flet build macos --yes`
3. 패키징·CI 변경 시: `build/flutter/app/app.zip`, `build/flutter/pubspec.yaml` 확인

## 패키징 제약

- `main.py`는 Flet 엔트리포인트로 저장소 루트에 유지합니다.
- app/package exclude 규칙은 동등한 대안 없이 제거하지 마십시오.
- 생성된 Flutter shell은 `pyproject.toml`의 `tool.flet.flutter.pubspec` override를 사용합니다.

## CI 제약

- CI는 `uvx --from "flet-cli==0.83.1"`로 빌드합니다 (`0.84.0`에서 serious_python 회귀).
- macOS 빌드는 `macos-15`를 사용합니다.
- macOS CI 네이티브 컴파일 실패 시 Python 코드보다 플러그인 버전을 먼저 확인합니다.
- `build-desktop.yml`: 일반 push/PR에서 빌드 검증만, artifact 미업로드.
- GitHub Release: `release-desktop.yml`의 `v*` 태그 push에서만 생성.
- 공개 macOS 배포물은 `release-desktop.yml` 결과만 사용합니다.

## 의존성 override (임의 제거 금지)

```toml
[tool.flet.flutter.pubspec.dependency_overrides]
connectivity_plus = "7.0.0"
device_info_plus = "12.3.0"
```

`connectivity_plus 7.1.1`에서 `NWPath has no member 'isUltraConstrained'` CI 실패 발생.

## 기능 불변 조건

- 정규화 시 기존 파일을 덮어쓰지 않습니다.
- rename 연속 실패 시 롤백합니다.
- Bulk fix는 자식을 부모보다 먼저 처리합니다.
- 실시간 감시와 bulk fix는 동일 핵심 rename 로직을 공유합니다.
- 최종 macOS 릴리스 검증은 zip 압축 해제 후 Gatekeeper 통과까지 포함합니다.
