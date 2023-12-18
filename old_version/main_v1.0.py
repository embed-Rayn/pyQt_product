import sys
import os
import time

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6 import QtGui
from glob import glob
import msvcrt
import subprocess

form_class = uic.loadUiType("test_v1.0.ui")[0]


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)

        self.setFixedWidth(855)
        self.setFixedHeight(402)

        self.pix_logo = QtGui.QPixmap("ico_imgs/logo.png")
        self.icon_upload = QtGui.QIcon("ico_imgs/File_Upload_icon.svg").pixmap(QSize(15, 15))
        self.icon_excute = QtGui.QIcon("ico_imgs/analysis.svg")
        self.lbl_logo.setPixmap(self.pix_logo.scaled(self.lbl_logo.size(), Qt.AspectRatioMode(2)))
        self.lbl_upload.setPixmap(self.icon_upload)
        self.btn_execute.setIcon(self.icon_excute)
        self.btn_execute.setIconSize(QSize(30, 30))

        self.input_file_path = ""
        self.output_file_path = ""

        self.btn_browse1.clicked.connect(self.browse_in)
        self.btn_browse2.clicked.connect(self.browse_out)
        self.btn_execute.clicked.connect(self.push_execute)
        self.lineEdit_output.setReadOnly(True)
        self.lineEdit_input.setReadOnly(True)
        self.btn_execute.setEnabled(False)

        self.isSetInput = False
        self.isSetOutput = False

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.DropAction(0x1))
            e.accept()
            # Workaround for OSx dragging and dropping
            dir_path = str(e.mimeData().urls()[0].toLocalFile())
            if os.path.isdir(dir_path):
                dir_path = dir_path.replace("/", os.sep)
                if not self.isSetInput:
                    self.input_file_path = dir_path
                    self.lineEdit_input.setText(self.input_file_path)
                    self.isSetInput = True
                    self.lbl_upload.setVisible(False)
                elif not self.isSetOutput:
                    self.output_file_path = dir_path
                    self.lineEdit_output.setText(self.output_file_path)
                    self.btn_execute.setEnabled(True)
                    self.isSetOutput = True
        else:
            e.ignore()

    def browse_in(self):
        try:
            path = QFileDialog.getExistingDirectory(self, 'Open Directory', os.getenv('HOME'))
            self.input_file_path = path
            self.isSetInput = True
            self.lbl_upload.setVisible(False)
            if self.isSetInput and self.isSetOutput:
                self.btn_excute.setEnabled(True)
        except:
            self.input_file_path = "wrong path"
            self.isSetInput = False
        if self.input_file_path == "":
            self.isSetInput = False
        self.lineEdit_input.setText(self.input_file_path)

    def browse_out(self):
        try:
            path = QFileDialog.getExistingDirectory(self, 'Open Directory', os.getenv('HOME'))
            self.output_file_path = path
            self.isSetOutput = True
            if self.isSetInput and self.isSetOutput:
                self.btn_execute.setEnabled(True)
        except:
            self.output_file_path = "wrong path"
            self.isSetOutput = False
        self.lineEdit_output.setText(self.output_file_path)

    def make_yaml(self, input_path, output_path):
        string = f"input_path: {input_path}\noutput_path: {output_path}\nbatchsize: 16\nsave_extra_l3_data: true"
        with open("config.yaml", "w", encoding="utf-8") as yaml:
            yaml.write(string)


    def run_model(self, home_dir):
        self.pgbar_download.setMinimum(0)
        self.pgbar_download.setMaximum(0)
        self.pgbar_download.setValue(0)
        os.chdir(home_dir)
        run_cmd = f"\"{home_dir}{os.sep}L3Analyzer_remote_license.exe\""
        os.system(run_cmd)
        # process = subprocess.Popen(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        #
        # while True:
        #     output = process.stdout.readline().decode('utf-8')
        #     if output == '' and process.poll() is not None:
        #         break
        #     if output:
        #         print(output.strip())
        #
        # process.wait()

    def push_execute(self):


        input_path = f"{self.input_file_path}{os.sep}Stomach*{os.sep}*"
        output_path = f"{self.output_file_path}{os.sep}L3Data{os.sep}Stomach*"
        len_input_dir = glob(input_path)
        len_input_dir = len(len_input_dir)

        home_dir = "C:\\Users\\qwe14\\OneDrive\\바탕 화면\\iAID-인수인계-소스코드\\소스코드\\L3-분석-서비스\\L3Measurement\\x64\\Release"
        os.chdir(home_dir)
        self.make_yaml(self.input_file_path, self.output_file_path)
        os.system('chcp 65001')
        self.btn_execute.setEnabled(False)
        os.chdir(self.output_file_path)
        del_cmd = f"del /s /q *"
        os.system(del_cmd)
        for dir_p in os.listdir("."):
            del_cmd = f"rmdir /s /q \"{dir_p}\""
            os.system(del_cmd)
        self.run_model(home_dir)
        msvcrt.putch(b"1")

        self.pgbar_download.setMaximum(100)
        self.pgbar_download.setValue(100)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec()
