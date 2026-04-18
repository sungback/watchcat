import flet as ft
import sys

from watchcat_app import (
    NFCConverterHandler,
    fix_path,
    main,
    pick_folder_mac_native,
    run_bulk_fix,
    visualize_nfd,
)


if __name__ == "__main__":
    try:
        ft.run(main)
    except Exception as e:
        print(f"Critical App Error: {e}")
    finally:
        sys.exit(0)
