import pip._internal as pip

print("Installing dependencies...")
for module in ["PyQt5", "PyQtWebEngine", "nuitka", "PIL", "requests"]:
    pip.main(['install', module])

from PIL import Image
import os, random, sys

AppIndex = os.path.isfile(os.path.join("resources", "index.html"))
if AppIndex:
    sys.exit(print("Make sure you have a index.html file in the resources folder."))

# Check if the correct amount of arguments were provided
if len(sys.argv) != 3 and len(sys.argv) != 1:
    print("Usage: python3 configure.py name \"description\"\nOr python3 configure.py")
    sys.exit(1)

AppName = sys.argv[1] if len(sys.argv) > 1 else input("Type the name of your web app: ")[:32]
AppDescription = sys.argv[2] if len(sys.argv) > 2 else input("Briefly describe your app: ")[:64]
AppPort = random.randint(32768, 61000)

input("Copy the icon to the main folder and name it \"icon.png\".\nPress Enter when you're done")

with Image.open("icon.png") as img:
    img = img.resize((256, 256))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    _, ext = os.path.splitext("icon.png")
    if ext.lower() != '.png':
        output_path = output_path + '.png'
    
    img.save("icon.png")

with open("app.desktop", "w") as DesktopFile:
    DesktopFile.write(f"[Desktop Entry]\nVersion=1.0\nName={AppName}\nComment={AppDescription}\nExec=main.bin\nIcon=icon\nTerminal=false\nType=Application\nCategories=Internet;")

with open("window.py", "w") as WindowScript:
    WindowScript.write(f"import sys\nfrom PyQt5.QtCore import QUrl\nfrom PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget\nfrom PyQt5.QtWebEngineWidgets import QWebEngineView\n\nclass JotaleaWebView(QMainWindow):\n    def __init__(self, *args, **kwargs):\n        super(JotaleaWebView, self).__init__(*args, **kwargs)\n        self.browser = QWebEngineView()\n        self.browser.setUrl(QUrl(\"http://localhost:{AppPort}/resources\"))        self.setWindowTitle({AppName})\n        self.setCentralWidget(self.browser)\n\napp = QApplication([])\nwindow = JotaleaWebView()\nwindow.show()\n\nsys.exit(app.exec_())")

with open("server.py", "w") as ServerScript:
    ServerScript.write(f"import http.server, socketserver, time\n\nPORT = {AppPort}\n\nhandler = http.server.SimpleHTTPRequestHandler\n\ntry:\n    with socketserver.TCPServer(("", PORT), handler) as httpd:\n        print(f\"[SERVER] HTTP server started on port {PORT}\")\n        try:\n            httpd.serve_forever()\n        except KeyboardInterrupt:\n            print(\"\n[SERVER] HTTP server stopped by user\")\nexcept OSError:\n    print(\"[SERVER] Server already running\")\n    while True:\n        time.sleep(120)")

with open("main.py", "w") as MainScript:
    content = """
import subprocess, signal, os, time

child_processes = []

def sigint_handler(sig, frame):
    print("\n[ HOST ] Main program interrupted. Terminating processes...")
    for pid in child_processes:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    
    exit(0)

def child_process_finished(signum, frame):
    print("[ HOST ] One of the child processes has been terminated.")
    print("[ HOST ] Terminating the main process...")
    sigint_handler(signal.SIGINT, None)

signal.signal(signal.SIGINT, sigint_handler)

child_command_1 = ["./window.bin"]
child_command_2 = ["./server.bin"] # ["./python3.12.3-cp312-cp312-manylinux2014_x86_64.AppImage", "-m", "http.server", "62456"]

child_process_1 = subprocess.Popen(child_command_1)
child_processes.append(child_process_1.pid)

child_process_2 = subprocess.Popen(child_command_2)
child_processes.append(child_process_2.pid)

signal.signal(signal.SIGCHLD, child_process_finished)

while True:
    all_finished = all(os.waitpid(pid, os.WNOHANG)[0] != 0 for pid in child_processes)

    if all_finished:
        break
    
    print("[ HOST ] Main process running...")
    time.sleep(1)

print("[ HOST ] Main process terminated sucessfully.")
"""
    MainScript.write(content)

with open("AppRun", "w") as AppRunFile:
    content = """
#!/bin/sh

DIR=$(dirname "$(readlink -f "$0")")
cd "$DIR"
chmod +x main.bin
./main.bin
exit $?
"""
    AppRunFile.write(content)

import subprocess
subprocess.run(["chmod", "+x", "AppRun"])

# https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
