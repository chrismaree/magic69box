import time
import os
import sys
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path, python_interpreter):
        self.script_path = os.path.abspath(script_path)
        self.python_interpreter = python_interpreter
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.kill()
            self.process.wait()
        self.process = subprocess.Popen([self.python_interpreter, self.script_path])

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == self.script_path:
            print("Detected change in script, restarting...")
            self.start_process()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python watchDog.py [python_interpreter] [script_path]")
        sys.exit(1)

    python_interpreter = sys.argv[1]
    script_path = sys.argv[2]

    observer = Observer()
    event_handler = ChangeHandler(script_path, python_interpreter)
    observer.schedule(event_handler, os.path.dirname(script_path), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()

    observer.join()
