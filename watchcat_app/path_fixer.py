import os
import unicodedata

from .unicode_utils import visualize_nfd


def _paths_point_to_same_entry(path_a, path_b):
    try:
        return os.path.samefile(path_a, path_b)
    except (FileNotFoundError, OSError):
        return False


def _build_temp_path(directory, base_name):
    candidate = os.path.join(directory, f"{base_name}.kfix_tmp")
    suffix = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base_name}.kfix_tmp{suffix}")
        suffix += 1
    return candidate


def fix_path(src_path, log_callback):
    """NFD 파일명을 NFC로 교정. 교정 시 True 반환."""
    if not src_path or not os.path.exists(src_path):
        return False

    directory, filename = os.path.split(src_path)

    if filename.endswith(".kfix_tmp"):
        return False

    nfc_name = unicodedata.normalize("NFC", filename)

    if filename == nfc_name:
        return False

    new_path = os.path.join(directory, nfc_name)
    if os.path.exists(new_path) and not _paths_point_to_same_entry(src_path, new_path):
        log_callback(f"⚠️ 이름 충돌로 건너뜀: {filename} -> {nfc_name}")
        return False

    temp_path = _build_temp_path(directory, nfc_name)
    renamed_to_temp = False

    try:
        os.rename(src_path, temp_path)
        renamed_to_temp = True
        os.rename(temp_path, new_path)
        visual_nfd_name = visualize_nfd(filename)
        log_callback(f"✅ 교정 완료: {visual_nfd_name} -> {nfc_name}")
        return True
    except Exception as e:
        if renamed_to_temp and os.path.exists(temp_path):
            try:
                os.rename(temp_path, src_path)
            except Exception as rollback_error:
                log_callback(
                    f"❌ 에러 발생 ({filename}): {str(e)} / 롤백 실패: {rollback_error}"
                )
                return False
        log_callback(f"❌ 에러 발생 ({filename}): {str(e)}")
        return False


def run_bulk_fix(root_path, log_callback, done_callback):
    """폴더 전체를 순회하며 NFD 파일명/폴더명을 일괄 교정."""
    scanned = 0
    fixed = 0

    # topdown=False: 하위 경로부터 처리해야 상위 폴더 rename 시 경로 깨짐 방지
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        for name in filenames:
            scanned += 1
            if fix_path(os.path.join(dirpath, name), log_callback):
                fixed += 1
        for name in dirnames:
            scanned += 1
            if fix_path(os.path.join(dirpath, name), log_callback):
                fixed += 1

    done_callback(scanned, fixed)
