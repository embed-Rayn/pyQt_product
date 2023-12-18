import sys
import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6 import QtGui
import time
from glob import glob
import asyncio

form_class = uic.loadUiType("gui.ui")[0]


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)

        self.setFixedWidth(855)
        self.setFixedHeight(482)

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

    async def check_file_count(self, output_path, len_input_dir):
        time_val = 0
        while True:
            time_val += 1
            len_output_dir = glob(output_path)
            len_output_dir = len(len_output_dir)
            percent = int(len_output_dir / len_input_dir * 100)
            self.pgbar_download.setValue(percent)
            time.sleep(1)
            if time_val < 60:
                time_string = f"Time: {time_val}s"
            else:
                time_string = f"Time: {time_val // 60:02d}m {time_val % 60:02d}s"
            self.lbl_time.setText(time_string)
            if percent == 100:
                break

    async def run_model(self, home_dir):
        os.chdir(home_dir)
        run_cmd = f"\"{home_dir}{os.sep}L3Analyzer_remote_license.exe\""
        os.system(run_cmd)

    def push_execute(self):
        input_path = f"{self.input_file_path}{os.sep}*{os.sep}*"
        output_path = f"{self.output_file_path}{os.sep}L3Data{os.sep}*"
        len_input_dir = glob(input_path)
        len_input_dir = len(len_input_dir)
        self.lbl_num_input.setText(f"Number of Input File: {len_input_dir}")

        home_dir = os.path.abspath("../x64/Release")
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
        loop = asyncio.get_event_loop()  # 이벤트 루프를 얻음
        self.check_file_count(output_path, len_input_dir)
        loop.run_until_complete(self.run_model(home_dir))  # print_add가 끝날 때까지 이벤트 루프를 실행
        loop.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec()
