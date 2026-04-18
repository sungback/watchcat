import os
import sys
import time
import threading
import subprocess
import unicodedata
import flet as ft
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")


# --- NFD 시각화용 자모 매핑표 (유니코드 호환 자모) ---
JAMO_MAP = {
    # 초성
    0x1100: 'ㄱ', 0x1101: 'ㄲ', 0x1102: 'ㄴ', 0x1103: 'ㄷ', 0x1104: 'ㄸ',
    0x1105: 'ㄹ', 0x1106: 'ㅁ', 0x1107: 'ㅂ', 0x1108: 'ㅃ', 0x1109: 'ㅅ',
    0x110A: 'ㅆ', 0x110B: 'ㅇ', 0x110C: 'ㅈ', 0x110D: 'ㅉ', 0x110E: 'ㅊ',
    0x110F: 'ㅋ', 0x1110: 'ㅌ', 0x1111: 'ㅍ', 0x1112: 'ㅎ',
    # 중성
    0x1161: 'ㅏ', 0x1162: 'ㅐ', 0x1163: 'ㅑ', 0x1164: 'ㅒ', 0x1165: 'ㅓ',
    0x1166: 'ㅔ', 0x1167: 'ㅕ', 0x1168: 'ㅖ', 0x1169: 'ㅗ', 0x116A: 'ㅘ',
    0x116B: 'ㅙ', 0x116C: 'ㅚ', 0x116D: 'ㅛ', 0x116E: 'ㅜ', 0x116F: 'ㅝ',
    0x1170: 'ㅞ', 0x1171: 'ㅟ', 0x1172: 'ㅠ', 0x1173: 'ㅡ', 0x1174: 'ㅢ',
    0x1175: 'ㅣ',
    # 종성
    0x11A8: 'ㄱ', 0x11A9: 'ㄲ', 0x11AA: 'ㄳ', 0x11AB: 'ㄴ', 0x11AC: 'ㄵ',
    0x11AD: 'ㄶ', 0x11AE: 'ㄷ', 0x11AF: 'ㄹ', 0x11B0: 'ㄺ', 0x11B1: 'ㄻ',
    0x11B2: 'ㄼ', 0x11B3: 'ㄽ', 0x11B4: 'ㄾ', 0x11B5: 'ㄿ', 0x11B6: 'ㅀ',
    0x11B7: 'ㅁ', 0x11B8: 'ㅂ', 0x11B9: 'ㅄ', 0x11BA: 'ㅅ', 0x11BB: 'ㅆ',
    0x11BC: 'ㅇ', 0x11BD: 'ㅈ', 0x11BE: 'ㅊ', 0x11BF: 'ㅋ', 0x11C0: 'ㅌ',
    0x11C1: 'ㅍ', 0x11C2: 'ㅎ'
}


def visualize_nfd(text):
    """
    NFD 문자열을 눈에 보이는 독립 자소로 치환합니다.
    폰트 엔진이 자소를 강제로 합치는 것(Ligature)을 방지하기 위해
    매 자소 뒤에 'Zero-Width Non-Joiner (\u200C)'를 삽입합니다.
    """
    result = ""
    for char in text:
        code = ord(char)
        if code in JAMO_MAP:
            # 호환 자모로 변경 후 결합 방지 기호(ZWNJ) 추가
            result += JAMO_MAP[code] + "\u200C"
        else:
            result += char
    return result


class NFCConverterHandler(FileSystemEventHandler):
    def __init__(self, log_callback):
        super().__init__()
        self.log_callback = log_callback

    def process_path(self, src_path):
        if not src_path or not os.path.exists(src_path):
            return

        directory, filename = os.path.split(src_path)

        if filename.endswith('.kfix_tmp'):
            return

        nfc_name = unicodedata.normalize('NFC', filename)

        if filename != nfc_name:
            new_path = os.path.join(directory, nfc_name)
            temp_path = os.path.join(directory, nfc_name + ".kfix_tmp")

            try:
                os.rename(src_path, temp_path)
                os.rename(temp_path, new_path)

                # 원본 파일명(NFD)을 풀어서 시각화
                visual_nfd_name = visualize_nfd(filename)

                # 시각화된 NFD 이름 -> 완성형 이름으로 로그 출력
                self.log_callback(f"✅ 교정 완료: {visual_nfd_name} -> {nfc_name}")
            except Exception as e:
                self.log_callback(f"❌ 에러 발생 ({filename}): {str(e)}")

    def on_created(self, event):
        if not event.is_directory:
            self.process_path(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.process_path(event.dest_path)


def pick_folder_mac_native():
    """Use AppleScript on macOS first to avoid desktop dialog quirks."""
    script = 'POSIX path of (choose folder with prompt "감시할 폴더를 선택하세요")'
    result = subprocess.check_output(["osascript", "-e", script], text=True).strip()
    return result or None


def main(page: ft.Page):
    page.title = "K-Fixer: 한글 자소 분리 해결사"
    page.window.width = 600
    page.window.height = 550
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30

    state = {"observer": None, "is_running": False}

    log_list = ft.ListView(expand=True, spacing=5, padding=10)

    def append_log(message):
        timestamp = time.strftime("%H:%M:%S")
        log_list.controls.append(
            ft.Text(f"[{timestamp}] {message}", size=12, font_family="monospace")
        )
        page.update()

    def on_path_change(e):
        # 경로가 입력되면 시작 버튼 활성화
        start_btn.disabled = not bool(selected_path_input.value.strip())
        page.update()

    def set_selected_path(path):
        selected_path_input.value = os.path.normpath(path)
        start_btn.disabled = not bool(selected_path_input.value.strip())
        page.update()

    # FilePicker 대신 직접 입력 가능한 TextField 사용
    selected_path_input = ft.TextField(
        label="감시할 폴더 경로",
        hint_text="직접 입력하거나 좌측 아이콘을 클릭하세요.",
        expand=True,
        text_size=13,
        on_change=on_path_change
    )

    async def pick_folder(e):
        selected_path = None

        if IS_MACOS:
            try:
                selected_path = pick_folder_mac_native()
            except subprocess.CalledProcessError:
                # 사용자가 macOS 폴더 선택 창에서 '취소'를 누른 경우 무시
                return
            except (FileNotFoundError, OSError):
                # AppleScript 사용이 불가능한 환경에서는 FilePicker로 폴백
                selected_path = None

        if selected_path is None:
            try:
                selected_path = await ft.FilePicker().get_directory_path(
                    dialog_title="감시할 폴더를 선택하세요"
                )
            except Exception as ex:
                append_log(f"❌ 폴더 선택창을 열지 못했습니다: {ex}")
                return

        if selected_path:
            set_selected_path(selected_path)

    def toggle_monitoring(e):
        if not state["is_running"]:
            path = selected_path_input.value.strip()
            if not os.path.isdir(path):
                append_log("❌ 유효한 폴더 경로를 입력해주세요.")
                return

            handler = NFCConverterHandler(append_log)
            state["observer"] = Observer()
            state["observer"].schedule(handler, path, recursive=True)

            threading.Thread(target=state["observer"].start, daemon=True).start()

            state["is_running"] = True
            start_btn.text = "감시 중지"
            start_btn.icon = ft.Icons.STOP_CIRCLE
            start_btn.color = ft.Colors.RED
            path_btn.disabled = True
            selected_path_input.disabled = True
            append_log(f"🚀 감시 시작: {path}")
        else:
            if state["observer"]:
                state["observer"].stop()
                state["observer"].join()

            state["is_running"] = False
            start_btn.text = "감시 시작"
            start_btn.icon = ft.Icons.PLAY_ARROW_ROUNDED
            start_btn.color = ft.Colors.BLUE
            path_btn.disabled = False
            selected_path_input.disabled = False
            append_log("🛑 감시가 중지되었습니다.")

        page.update()

    path_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        icon_color=ft.Colors.BLUE_GREY_700,
        on_click=pick_folder,
        tooltip="폴더 선택" if IS_WINDOWS else "폴더 선택"
    )

    start_btn = ft.Button(
        "감시 시작",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        on_click=toggle_monitoring,
        disabled=True
    )

    page.add(
        ft.Column([
            ft.Text("K-Fixer", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("맥-윈도우 한글 자소 분리 문제를 실시간으로 해결합니다.", size=14, color=ft.Colors.GREY_600),
            ft.Divider(height=20, thickness=1),

            ft.Row([path_btn, selected_path_input], vertical_alignment=ft.CrossAxisAlignment.CENTER),

            ft.Container(height=10),
            start_btn,
            ft.Container(height=20),

            ft.Text("작업 로그", weight=ft.FontWeight.W_600),
            ft.Container(
                content=log_list,
                bgcolor=ft.Colors.GREY_50,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                expand=True
            )
        ], expand=True)
    )


if __name__ == "__main__":
    try:
        ft.run(main)
    except Exception as e:
        print(f"Critical App Error: {e}")
    finally:
        sys.exit(0)
