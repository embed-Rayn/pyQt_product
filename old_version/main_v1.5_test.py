import sys
import os
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6 import QtGui
import time
from glob import glob
import subprocess
import re


form_class = uic.loadUiType("4test.ui")[0]


class TimerThread(QThread):
    update_signal = pyqtSignal(int)

    def run(self):
        i = 0
        while True:
            i += 1
            self.update_signal.emit(i)
            time.sleep(1)


class ModelThread(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, parent, home_dir, output_file_path):
        super().__init__(parent)
        self.home_dir = home_dir
        self.output_file_path = output_file_path
        self.should_stop = False

    def run(self):
        os.chdir(self.home_dir)
        run_cmd = f"\"{self.home_dir}{os.sep}L3Analyzer_remote_license.exe\""
        sp = subprocess.Popen(run_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        (stdout, stderr) = sp.communicate()
        results = stdout.decode('euc-kr')
        if ". . ." in results:
            self.finished.emit(True)
            self.quit()
        sp.stdin.close()
        os.startfile(self.output_file_path)


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)
        self.setWindowTitle("IAID Sarcopenia")

        self.setFixedWidth(855)
        self.setFixedHeight(520)
        # self.setTitle("IAID L3Measure")

        font = QtGui.QFont("Arial", 17)
        self.lbl_input.setFont(font)
        self.lbl_ouput.setFont(font)
        self.lbl_num_input.setFont(font)
        self.lbl_num_output.setFont(font)
        self.lbl_time.setFont(font)
        self.lbl_batch.setFont(font)

        self.pix_logo = QtGui.QPixmap("ico_imgs/logo.png")
        self.icon_upload = QtGui.QIcon("ico_imgs/File_Upload_icon.svg").pixmap(QSize(15, 15))
        self.icon_execute = QtGui.QIcon("ico_imgs/analysis.svg")
        self.lbl_logo.setPixmap(self.pix_logo.scaled(self.lbl_logo.size(), Qt.AspectRatioMode(1)))
        self.lbl_upload.setPixmap(self.icon_upload)
        self.btn_execute.setIcon(self.icon_execute)
        self.btn_execute.setIconSize(QSize(30, 30))

        self.input_file_path = ""
        self.output_file_path = ""

        self.btn_browse1.clicked.connect(self.browse_in)
        self.btn_browse2.clicked.connect(self.browse_out)
        self.btn_execute.clicked.connect(self.push_execute)
        self.btn_16.clicked.connect(self.on_btn16)
        self.btn_32.clicked.connect(self.on_btn32)
        self.btn_64.clicked.connect(self.on_btn64)
        self.btn_128.clicked.connect(self.on_btn128)

        self.lineEdit_output.setReadOnly(True)
        self.lineEdit_input.setStyleSheet("color: gray;")
        self.lineEdit_input.setReadOnly(True)
        self.btn_execute.setEnabled(False)
        self.toggle_batch_size = [True, False, False, False]

        self.isSetInput = False
        self.isSetOutput = False

        self.prev_percent = 0
        self.prev_time_min = 0

        self.gui_home_dir = os.path.abspath(".")

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
                    self.lineEdit_input.setStyleSheet("color: black;")
                    self.lineEdit_input.setText(self.input_file_path)
                    self.isSetInput = True
                    self.lbl_upload.setVisible(False)
                elif not self.isSetOutput:
                    self.output_file_path = dir_path
                    self.lineEdit_output.setText(self.output_file_path)
                    self.isSetOutput = True
                if self.isSetInput and self.isSetOutput:
                    self.btn_execute.setEnabled(True)
        else:
            e.ignore()

    def occur_path_error(self, sort_of):
        if sort_of == "input":
            self.isSetInput = False
        elif sort_of == "output":
            self.isSetOutput = False
        self.btn_execute.setEnabled(False)

    def browse_in(self):
        try:
            path = QFileDialog.getExistingDirectory(self, 'Open Directory', os.getenv('HOME'))
            self.input_file_path = path
            self.isSetInput = True
            self.lbl_upload.setVisible(False)
            self.lineEdit_input.setStyleSheet("color: black;")
            if self.isSetInput and self.isSetOutput:
                self.btn_execute.setEnabled(True)
        except:
            self.input_file_path = ""
            self.occur_path_error("input")
        if self.input_file_path == "":
            self.occur_path_error("input")
        self.lineEdit_input.setText(self.input_file_path)

    def browse_out(self):
        try:
            path = QFileDialog.getExistingDirectory(self, 'Open Directory', os.getenv('HOME'))
            self.output_file_path = path
            self.isSetOutput = True
            if self.isSetInput and self.isSetOutput:
                self.btn_execute.setEnabled(True)
        except:
            self.output_file_path = ""
            self.occur_path_error("output")
        if self.output_file_path == "":
            self.occur_path_error("output")
        self.lineEdit_output.setText(self.output_file_path)

    def make_rst_path(self):
        rst_path = os.listdir(self.output_file_path)

        pattern = r'^result\d\d$'
        digit_stack = []
        for dir_name in rst_path:
            matches = re.findall(pattern, dir_name)
            try:
                a = matches[0]
                digit_stack.append(a[-2:])
            except IndexError:
                pass
        i = 0

        while True:
            i += 1
            r_id = f"{i:02d}"
            if r_id not in digit_stack:
                path = f"{self.output_file_path}{os.sep}result{r_id}"
                self.output_path = f"{self.output_file_path}{os.sep}result{r_id}{os.sep}L3Data{os.sep}*"
                os.makedirs(path)
                self.output_file_path = path
                break

    def make_yaml(self):
        toggle = self.toggle_batch_size
        batch_size = 16
        for idx, val in enumerate(toggle):
            if val:
                batch_size = 2**(idx+4)
                break
        string = f"input_path: {self.input_file_path}\noutput_path: {self.output_file_path}\nbatchsize: {batch_size}\nsave_extra_l3_data: true"
        with open("config.yaml", "w", encoding="utf-8") as yaml:
            yaml.write(string)

    def update_progress(self, time_value):
        len_output_dir = glob(self.output_path)
        len_output_dir = len(len_output_dir)
        percent = int(len_output_dir / self.len_input_dir * 100)
        if self.prev_percent != percent:
            self.pgbar_download.setValue(percent)
            self.prev_percent = percent
        time_min = time_value // 60
        if time_value < 60:
            time_string = f"Time: {time_value:02d}s"
            self.lbl_time.setText(time_string)
        else:
            time_sec = time_value % 60
            time_string = f"Time: {time_min:02d}m{time_sec:02d}s"
            self.lbl_time.setText(time_string)
            self.prev_time_min = time_min

    def update_output_dir_num(self):
        len_output_dir = len(glob(self.output_path))
        prefix = self.lbl_num_output.text()
        self.lbl_num_output.setText(f"{prefix} {len_output_dir}")
        self.finish_task()

    def finish_task(self):
        self.btn_browse1.setEnabled(True)
        self.btn_browse2.setEnabled(True)
        self.btn_execute.setEnabled(False)
        self.lineEdit_output.setText("")
        self.lineEdit_input.setText("")
        self.isSetInput = False
        self.isSetOutput = False
        os.chdir(self.gui_home_dir)

    def push_execute(self):
        input_path = f"{self.input_file_path}{os.sep}*{os.sep}*"
        entries = glob(input_path)
        directories = [entry for entry in entries if os.path.isdir(entry)]
        self.len_input_dir = len(directories)
        self.lbl_num_input.setText(f"No. Input File:")
        self.lbl_num_output.setText(f"No. Output File:")
        prefix = self.lbl_num_input.text()
        self.lbl_num_input.setText(f"{prefix} {self.len_input_dir}")

        home_dir = os.path.abspath("../../../x64/Release")
        os.chdir(home_dir)
        self.make_rst_path()
        self.make_yaml()
        os.system('chcp 65001')
        self.btn_execute.setEnabled(False)
        self.btn_browse1.setEnabled(False)
        self.btn_browse2.setEnabled(False)
        os.chdir(self.output_file_path)
        self.time_thread = TimerThread(self)
        self.time_thread.update_signal.connect(self.update_progress)
        self.time_thread.start()

        self.model_thread = ModelThread(self, home_dir, self.output_file_path)
        self.model_thread.finished.connect(self.time_thread.terminate)
        self.model_thread.finished.connect(self.update_output_dir_num)
        self.model_thread.start()
        for sec in range(4):
            self.raise_()
            time.sleep(0.2)

    def on_btn16(self):
        btn_list = [self.btn_16, self.btn_32, self.btn_64, self.btn_128]
        self.toggle_batch_size = [True, False, False, False]
        for idx, btn in enumerate(btn_list):
            if self.toggle_batch_size[idx]:
                btn.setChecked(True)
            else:
                btn.setChecked(False)


    def on_btn32(self):
        btn_list = [self.btn_16, self.btn_32, self.btn_64, self.btn_128]
        self.toggle_batch_size = [False, True, False, False]
        for idx, btn in enumerate(btn_list):
            if self.toggle_batch_size[idx]:
                btn.setChecked(True)
            else:
                btn.setChecked(False)


    def on_btn64(self):
        btn_list = [self.btn_16, self.btn_32, self.btn_64, self.btn_128]
        self.toggle_batch_size = [False, False, True, False]
        for idx, btn in enumerate(btn_list):
            if self.toggle_batch_size[idx]:
                btn.setChecked(True)
            else:
                btn.setChecked(False)


    def on_btn128(self):
        btn_list = [self.btn_16, self.btn_32, self.btn_64, self.btn_128]
        self.toggle_batch_size = [False, False, False, True]
        for idx, btn in enumerate(btn_list):
            if self.toggle_batch_size[idx]:
                btn.setChecked(True)
            else:
                btn.setChecked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec()



