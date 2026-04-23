# 빌드 가이드

## 로컬 빌드

```bash
flet build macos --yes
```

## CI 빌드

```bash
uvx --from "flet-cli==${FLET_CLI_VERSION}" flet build <target> --yes --verbose --clear-cache
```

CI는 `FLET_CLI_VERSION=0.83.1`을 고정합니다. 임의로 올리지 마십시오 (`0.84.0` 회귀 이력 있음).

## 빌드 후 확인

- `build/flutter/app/app.zip`: `.venv`, `.claude`, 테스트 파일 미포함 확인
- `build/flutter/pubspec.yaml`: Flutter 의존성 override 적용 확인
- macOS 배포 검증: zip 압축 해제 후 Gatekeeper 통과 확인 (staging `.app` 기준 아님)
