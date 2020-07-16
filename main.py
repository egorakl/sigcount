import sys
import os
import time
from PyQt5 import QtCore, QtWidgets
import pandas as pd

import sigcheck
import design


class SigApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.thread = QtCore.QThread()

        self.fileButton.clicked.connect(self.files_path)
        self.outputButton.clicked.connect(self.out_path)
        self.signatureButton.clicked.connect(self.signature_path)
        self.okButton.clicked.connect(self.check_ok)
        self.StartButton.clicked.connect(self.start_count)

    def pushmsg(self, msg):
        self.textBrowser.append(str(msg))

    def enable_ok(self, status):
        if status:
            self.okButton.setEnabled(True)

    def check_ok(self):
        self.textBrowser.clear()
        cont = True
        try:
            DIR = self.FilesPath.text()
            l = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
            self.textBrowser.append("{} files at {}".format(l, DIR))
            if l == 0:
                cont = False
        except FileNotFoundError:
            self.textBrowser.append("No file directory chosen!")
            cont = False
        
        if self.SigPath.text():
            self.textBrowser.append("Signature file: {}".format(self.SigPath.text()))
        else:
            self.textBrowser.append("No signature directory chosen!")
            cont = False

        if self.TablesPath.text():
            self.textBrowser.append("Output dir: {}".format(self.TablesPath.text()))
        else:
            self.textBrowser.append("No output directory chosen!")
            cont = False
        
        if self.CouplingCheck.checkState():
            self.textBrowser.append("Coupling: ON")
        else:
            self.textBrowser.append("Coupling: OFF")

        if self.StarValue.text().isdigit():
            self.textBrowser.append("* value: {}".format(self.StarValue.text()))
        else:
            self.StarValue.setText("1")
            self.textBrowser.append("* value: {}".format(self.StarValue.text()))
        
        if self.FragSize.text().isdigit():
            if int(self.FragSize.text()) == 0:
                self.textBrowser.append("Fragment size: the whole file")
            else:
                self.textBrowser.append("Fragment size: {} bytes".format(self.FragSize.text()))
        else:
            self.FragSize.clear()
            self.textBrowser.append("Fragment size is not chosen!")
            cont = False
        
        if cont:
            self.StartButton.setEnabled(True)
            self.textBrowser.append("\nPress Start to continue")
        else:
            self.StartButton.setEnabled(False)

    def files_path(self):
        self.FilesPath.clear()
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку")
        if directory:
            self.FilesPath.setText(directory)
    
    def signature_path(self):
        self.SigPath.clear()
        directory = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл", filter = "Text files (*.txt)")
        if directory[0]:
            self.SigPath.setText(directory[0])

    def out_path(self):
        self.TablesPath.clear()
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку")
        if directory:
            self.TablesPath.setText(directory)

    def start_count(self):

        self.okButton.setEnabled(False)
        self.StartButton.setEnabled(False)
        
        f_dir = self.FilesPath.text()
        pattern_txt_dir = self.SigPath.text()
        output_path = self.TablesPath.text()
        fragment_size = int(self.FragSize.text())
        star_len = int(self.StarValue.text())
        coupling = self.CouplingCheck.checkState()

        args = [f_dir, pattern_txt_dir, output_path, fragment_size, star_len, coupling]

        self.threadclass = ThreadClass(args = args)
        self.threadclass.start()
        self.threadclass.outmsg.connect(self.pushmsg)
        self.threadclass.finish_status.connect(self.enable_ok)




class ThreadClass(QtCore.QThread):
    outmsg = QtCore.pyqtSignal(str)
    finish_status = QtCore.pyqtSignal(bool)
    def __init__(self, args):
        super().__init__()
        self.args = args

    def sig_table(self, params):
        file_dir, pattern_txt, out_path, frag_size, star, coupling = params

        self.outmsg.emit("\nProcess started\n")
        time1 = time.time()
        patterns = []
        with open(pattern_txt, "r") as t:
            for line in t:
                pattern_str = line.rstrip('\n\t')
                if pattern_str:
                    patterns.append(pattern_str)
        columns = ['bytesize', 'start_offset', 'end_offset'] + patterns
        for file_name in os.listdir(file_dir):
            self.outmsg.emit("Processing \"{}\"...".format(file_name))
            d = file_dir + '/' + file_name
            bits = sigcheck.getbits(d, frag_size)
            data = []
            fr_start = 0
            fr_end = 0
            for frag in bits:
                bytesize = int(len(frag)/8)
                fr_end += bytesize-1
                row = [bytesize, fr_start, fr_end]
                fr_start += bytesize-1
                for patt in patterns:
                    s = sigcheck.subcount(frag, patt, star, coupling)
                    row.append(s)
                data.append(row)
            df = pd.DataFrame(data=data, columns=columns)
            table_path = out_path + '/' + file_name.replace(".", "-")+'-table.csv'
            self.outmsg.emit("Writing table: {}\n".format(table_path))
            df.to_csv(table_path, index=False)
        time2 = time.time()
        self.outmsg.emit("Done!\nTotal run: {} seconds".format(time2-time1))
        self.finish_status.emit(True)

    def run(self):
        self.sig_table(self.args)

        




def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = SigApp()
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':
    main()