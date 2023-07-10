from PyQt5 import uic, QtCore, QtWidgets, QtGui
import sys
import os
import socketserver
import subprocess
import re
import http.server

from PyQt5.QtWidgets import QWidget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('./res/template.ui', self)

        self.sendbtn.installEventFilter(self)
        self.selectbtn.installEventFilter(self)

        self.sendbtn.clicked.connect(self.send_func)
        self.selectbtn.clicked.connect(self.select_func)

    def sever_start(self):
        directory = "./"
        server_address = ('', 8000)
        os.chdir(directory)

        handler = http.server.SimpleHTTPRequestHandler

        # Start the HTTP server
        with socketserver.TCPServer(server_address, handler) as httpd:
            print(f"Serving HTTP on {server_address[0]}:{server_address[1]} from '{directory}'...")
            httpd.serve_forever()

    def send_func(self):
        self.ip_add.clear()
        result = subprocess.run(["netsh", "interface", "ip", "show", "addresses"], capture_output=True, text=True)

        # Extract the IPv4 address from the output
        ipv4_address = re.search(r"IP Address:\s+([\d.]+)", result.stdout)

        if ipv4_address:
            print("IPv4 Address:", ipv4_address.group(1))
            self.ip_add.setText(ipv4_address.group(1))
        else:
            print("IPv4 Address not found.")

    
    def select_func(self):
        return

App = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
App.exec_()