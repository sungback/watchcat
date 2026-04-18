import subprocess


def pick_folder_mac_native():
    """Use AppleScript on macOS first to avoid desktop dialog quirks."""
    script = 'POSIX path of (choose folder with prompt "감시할 폴더를 선택하세요")'
    result = subprocess.check_output(["osascript", "-e", script], text=True).strip()
    return result or None
