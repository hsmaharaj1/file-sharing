from PyQt5 import uic, QtCore, QtWidgets, QtGui
import sys
import os
import socketserver
import subprocess
import re
import http.server
import shutil
import requests
import socket
from bs4 import BeautifulSoup

# WorkerSignals class for defining custom signals
class WorkerSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

# Worker class for performing background tasks
class Worker(QtCore.QRunnable):
    def __init__(self, fun, *args, **kwargs):
        super(Worker, self).__init__()
        self.fun = fun
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.fun(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

# Main Class
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('./res/template.ui', self)

        self.pool = QtCore.QThreadPool.globalInstance() # For Multithreading Purpose

        self.sendbtn.clicked.connect(self.send_func)
        self.selectbtn.clicked.connect(self.select_func)
        self.receivebtn.clicked.connect(self.receive_func)

        self.model = QtGui.QStandardItemModel()
        self.files_list.setModel(self.model)

        self.files_list.setStyleSheet("QListView::item{color: white;}")

    def server_start(self):
        directory = "./temp_dir"
        server_address = ('', 8000)
        os.chdir(directory)

        handler = http.server.SimpleHTTPRequestHandler

        # Start the HTTP server
        with socketserver.TCPServer(server_address, handler) as self.httpd:
            print(f"Serving HTTP on {server_address[0]}:{server_address[1]} from '{directory}'...")
            self.httpd.serve_forever()

    def send_func(self):
        worker_server = Worker(self.server_start)
        worker_server.signals.finished.connect(self.server_finished)
        worker_server.signals.error.connect(self.server_error)
        self.pool.start(worker_server)

        self.ip_add.clear()
        ipv4_address = self.get_ipv4_address()
        if ipv4_address:
            print("IPv4 Address:", ipv4_address)
            self.address = ipv4_address + ':8000'
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

        item = QtGui.QStandardItem(os.path.basename(file_path))
        self.model.appendRow(item)
        print("File Copied to: ", new_file_path)

    def receive_func(self):
        ip = self.ip_add.toPlainText()
        print(ip)
        download_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Save Location", "", QtWidgets.QFileDialog.ShowDirsOnly)
        worker_download = Worker(self.download_data, url=ip, download_location=download_path)
        self.pool.start(worker_download)

    def download_data(self, url, download_location):
        modified_url = 'http://' + url
        print(modified_url)
        response = requests.get(modified_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a'):
            file_url = link.get('href')
            if file_url.endswith('/'):
                continue  # Skip directories

            file_name = os.path.basename(file_url)
            file_path = os.path.join(download_location, file_name)
            file_response = requests.get(modified_url + '/' + file_url)

            with open(file_path, 'wb') as file:
                file.write(file_response.content)

            print(f"Downloaded: {file_name}")

        print("All files downloaded successfully.")

    def server_finished(self):
        print("Server started successfully.")

    def server_error(self, error):
        print("Error occurred while starting the server:", error)

    def receive_finished(self):
        print("File receive completed successfully.")

    def receive_error(self, error):
        print("Error occurred while receiving files:", error)

    def closeEvent(self, event):
        self.pool.clear()
        try:
            if self.httpd is not None:
                self.httpd.shutdown()
            event.accept()
        except:
            return
    
    def get_ipv4_address(self):
        interfaces = socket.getaddrinfo(socket.gethostname(), None)
        for interface in interfaces:
            address = interface[4][0]
            if ':' not in address:
                return address
        return None

if __name__ == '__main__':
    App = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(App.exec_())
