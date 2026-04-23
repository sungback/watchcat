# 장애·수정 이력

- `fix_path()`: Unix에서 이미 존재하는 정규화 대상을 덮어쓰는 버그 → 충돌 감지 후 skip으로 수정.
- `fix_path()`: 두 번째 rename 실패 시 임시 파일 잔류 버그 → 롤백 로직 추가.
- Monitor: `Observer.start()`를 별도 스레드로 감싸 `join before start` 레이스 발생 → 래퍼 제거.
- CI: `serious_python` 패키징 실패 → `flet-cli` 버전 `0.83.1`로 고정.
- CI: Flutter 플러그인 컴파일 실패 → `connectivity_plus`, `device_info_plus` override 고정.
- 배포 검증: staging `.app`만 검증해 zip 재압축 후 Gatekeeper 실패 발생 → 릴리스 zip 기준으로 검증 기준 변경.
- 릴리스: 일반 push에서 GitHub Release 파일 미생성 확인 → `v*` 태그 push에서만 릴리스.
