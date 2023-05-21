import sys
import time
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent


class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event: FileCreatedEvent):
        super().on_created(event)

        print(f"{event.src_path} created, type {event.event_type}")


def reloads(signum, frame):
    print("realod")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    path = sys.argv[1] if len(sys.argv) > 1 else "."

    event_handler = FileEventHandler()

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while 1:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
