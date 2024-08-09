import os
import random
import requests
import shutil
import subprocess
import sys
from PIL import Image

# Check for command arguments
if len(sys.argv) != 3 and len(sys.argv) != 1:
    print("Usage: python3 configure.py name \"description\"\nOr python3 configure.py")
    sys.exit(1)

AppName = sys.argv[1] if len(sys.argv) > 1 else input("Type the name of your web app: ")[:32]
AppDescription = sys.argv[2] if len(sys.argv) > 2 else input("Briefly describe your app: ")[:64]

# Check if there are any missing dependencies
for module in ["PyQt5", "PyQtWebEngine", "nuitka", "PIL", "requests"]:
    try:
        if module == "PIL":
            __import__("PIL.Image")
        else:
            __import__(module)
    except ModuleNotFoundError:
        print(f"Module '{module}' is not installed.")

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
        except Exception as e:
            sys.exit(print(e))
        
        print(f"Module '{module}' installed successfully.")

# Check if there's an index.html file
if os.path.isfile(os.path.join("resources", "index.html")):
    sys.exit(print("Make sure you have an index.html file in the resources folder."))

# Pick a random port
AppPort = random.randint(32768, 61000)

# Extract code for server, window, and process manager, and apply the right port to both server and window
with open("server.py", "w") as ServerScript:
    ServerScript.write(f"import http.server, socketserver, time\n\nPORT = {AppPort}\n\nhandler = http.server.SimpleHTTPRequestHandler\n\ntry:\n    with socketserver.TCPServer(("", PORT), handler) as httpd:\n        print(f\"[SERVER] HTTP server started on port {PORT}\")\n        try:\n            httpd.serve_forever()\n        except KeyboardInterrupt:\n            print(\"\n[SERVER] HTTP server stopped by user\")\nexcept OSError:\n    print(\"[SERVER] Server already running\")\n    while True:\n        time.sleep(120)")

with open("window.py", "w") as WindowScript:
    WindowScript.write(f"import sys\nfrom PyQt5.QtCore import QUrl\nfrom PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget\nfrom PyQt5.QtWebEngineWidgets import QWebEngineView\n\nclass JotaleaWebView(QMainWindow):\n    def __init__(self, *args, **kwargs):\n        super(JotaleaWebView, self).__init__(*args, **kwargs)\n        self.browser = QWebEngineView()\n        self.browser.setUrl(QUrl(\"http://localhost:{AppPort}/resources\"))\n        self.setWindowTitle({AppName})\n        self.setCentralWidget(self.browser)\n\napp = QApplication([])\nwindow = JotaleaWebView()\nwindow.show()\n\nsys.exit(app.exec_())")

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

# Compile both
try:
    subprocess.run(
        [sys.executable, "-m", "nuitka", "--standalone", "server.py"],
        check=True
    )
    print(f"Successfully compiled server with Nuitka.")
    subprocess.run(
        [sys.executable, "-m", "nuitka", "--standalone", "window.py"],
        check=True
    )
    print(f"Successfully compiled window with Nuitka.")
    subprocess.run(
        [sys.executable, "-m", "nuitka", "--standalone", "main.py"],
        check=True
    )
    print(f"Successfully compiled main with Nuitka.")
except subprocess.CalledProcessError as e:
    print(f"An error occurred while compiling with Nuitka: {e}")
    sys.exit(1)

# Generate .desktop file
with open("app.desktop", "w") as DesktopFile:
    DesktopFile.write(f"[Desktop Entry]\nVersion=1.0\nName={AppName}\nComment={AppDescription}\nExec=main.bin\nIcon=icon\nTerminal=false\nType=Application\nCategories=Internet;")

# Generate AppRun file and grant execution permission
with open("AppRun", "w") as AppRunFile:
    content = "#!/bin/sh\n\nDIR=$(dirname \"$(readlink -f \"$0\")\")\ncd \"$DIR\"\nchmod +x main.bin\n./main.bin\nexit $?"
    AppRunFile.write(content)
subprocess.run(["chmod", "+x", "AppRun"])

# Ask for icon.png
input("Copy the icon to the main folder and name it \"icon.png\".\nPress Enter when you're done")

# Resize icon.png
with Image.open("icon.png") as img:
    img = img.resize((256, 256))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.save("icon.png")

# Download AppImageTool
try:
    response = requests.get("https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage", stream=True)
    response.raise_for_status()  # Check if the request was successful

    with open("appimagetool-x86_64.AppImage", 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    
    print(f"AppImageTool downloaded sucessfully")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

# Use AppImageTool to convert the whole program into an AppImage
subprocess.run(["chmod", "+x", "appimagetool-x86_64.AppImage"])
subprocess.run(["./appimagetool-x86_64.AppImage", "."])

# Move the final AppImage to ./bin directory
try:
    shutil.move("./appimagetool-x86_64.AppImage", "./bin/appimagetool-x86_64.AppImage")
    print(f"File moved from . to ./bin/")
except FileNotFoundError:
    print(f"File not found: ./appimagetool-x86_64.AppImage")
except PermissionError:
    print(f"Permission denied to move file.")
except Exception as e:
    print(f"An error occurred: {e}")

print(f"AppImage created at ./bin/{AppName}-x86_64.AppImage")
sys.exit()
