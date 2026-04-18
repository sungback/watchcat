from watchdog.events import FileSystemEventHandler

from .path_fixer import fix_path


class NFCConverterHandler(FileSystemEventHandler):
    def __init__(self, log_callback):
        super().__init__()
        self.log_callback = log_callback

    def on_created(self, event):
        if not event.is_directory:
            fix_path(event.src_path, self.log_callback)

    def on_moved(self, event):
        if not event.is_directory:
            fix_path(event.dest_path, self.log_callback)
