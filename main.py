from PyQt5 import uic, QtCore, QtWidgets, QtGui
import sys
import os
import socketserver
import subprocess
import re
import http.server
import shutil

# These two classes are for Multi-Threading Purposes
class WorkerSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()

class Worker(QtCore.QRunnable):
    def __init__(self, fun, *args, **kwargs):
        super(Worker, self).__init__()
        self.fun = fun
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    @QtCore.pyqtSlot()
    def run(self):
        self.fun(*self.args, **self.kwargs)
        self.signals.finished.emit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('./res/template.ui', self)

        self.pool = QtCore.QThreadPool.globalInstance() # For Multithreading Purpose

        self.sendbtn.installEventFilter(self)
        self.selectbtn.installEventFilter(self)

        self.sendbtn.clicked.connect(self.send_func)
        self.selectbtn.clicked.connect(self.select_func)

    def server_start(self):
        directory = "./temp_dir"
        server_address = ('', 8000)
        os.chdir(directory)

        handler = http.server.SimpleHTTPRequestHandler

        # Start the HTTP server
        with socketserver.TCPServer(server_address, handler) as httpd:
            print(f"Serving HTTP on {server_address[0]}:{server_address[1]} from '{directory}'...")
            httpd.serve_forever()
            return

    def send_func(self):
        # self.server_start()
        worker_server = Worker(self.server_start)
        self.pool.start(worker_server)
        self.ip_add.clear()
        result = subprocess.run(["netsh", "interface", "ip", "show", "addresses"], capture_output=True, text=True)

        # Extract the IPv4 address from the output
        ipv4_address = re.search(r"IP Address:\s+([\d.]+)", result.stdout)

        if ipv4_address:
            print("IPv4 Address:", ipv4_address.group(1))
            self.address = ipv4_address.group(1) + ':8000' 
            self.ip_add.setText(self.address)
        else:
            print("IPv4 Address not found.")

    
    def select_func(self):
        file_url, _ = QtWidgets.QFileDialog.getOpenFileUrl(self, "Select Files")
        file_path = file_url.toLocalFile()
        print(file_path)

        #Copying to a new Directory
        temp_dir = os.path.join(os.getcwd(), "temp_dir")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        os.makedirs(temp_dir, exist_ok=True)

        new_file_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copy2(file_path, new_file_path)

        print("File Copied to: ", new_file_path)

App = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
App.exec_()