from PyQt5 import QtWidgets
from pathlib import Path

import sys
import os

from config import terminal_config

from terminal import *

import threading

ui_file = "/Users/philippmochti/PycharmProjects/ChargeTerminal/GUI.ui"


class ApplicationWindow(QtWidgets.QMainWindow):

    closeApp = pyqtSignal()

    def __init__(self):
        self.name = 0
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_UpdateGUI()
        self.ui.setupUi(self)
        self.CardReader = Terminal()

        self.ui.value_1.setText(str(terminal_config["value_1"]) + " pro Kaffee")
        self.ui.value_2.setText(str(terminal_config["value_2"]) + " pro Kaffee")
        self.ui.value_service.setText(str(terminal_config["service"]))
        self.ui.page_1.setText(str(terminal_config["ChipPage_1"]))
        self.ui.page_2.setText(str(terminal_config["ChipPage_2"]))

        self.ui.value_1.clicked.connect(self.CardReader.setValue1)
        self.ui.value_2.clicked.connect(self.CardReader.setValue2)
        self.ui.value_service.clicked.connect(self.CardReader.setValueService)

        self.ui.page_1.clicked.connect(self.CardReader.setPage1)
        self.ui.page_2.clicked.connect(self.CardReader.setPage2)

        self.ui.Reset_Credit_1.clicked.connect(self.CardReader.reset_1)
        self.ui.Reset_Credit_2.clicked.connect(self.CardReader.reset_2)

        self.ui.Update.valueChanged.connect(self.update_spin_roll)


        self.CardReader.UpdateUi.connect(self.update_ui)
        self.CardReader.ShowPopup.connect(self.show_popup)
        self.ui.UpdateButton.clicked.connect(self.CardReader.write_to_chip)
        t = threading.Thread(target=self.terminal)
        t.start()

    def update_spin_roll(self):
        self.CardReader.value = self.ui.Update.value()

    def closeEvent(self, event):
        event.accept()

    def show_popup(self):
        self.text = ""
        self.okPressed = False
        self.text, self.okPressed = QInputDialog.getText(self, "ID: " + self.CardReader.ActiveCardId, "User Name:", QLineEdit.Normal, "")

        if self.okPressed:
            self.CardReader.store_new_user(self.text)
        else:
            self.CardReader.ActiveCardIdName = "unknown"

    def update_ui(self):
        self.ui.UserID.setText("Card ID: " + str(self.CardReader.ActiveCardId))
        self.ui.Credit_1.setText(str(self.CardReader.ActiveCardCredit_1))
        self.ui.Credit_2.setText(str(self.CardReader.ActiveCardCredit_2))
        self.ui.UserName.setText(self.CardReader.ActiveCardIdName)
        self.ui.SystemOutput.setText(str(self.CardReader.system_output))
        if str(self.CardReader.system_output) == "Connection Active":
            self.ui.SystemOutput.setStyleSheet("background-color: green")
        elif str(self.CardReader.system_output) == "Hardware not found - connected?":
            self.ui.SystemOutput.setStyleSheet("background-color: red")
        else:
            self.ui.SystemOutput.setStyleSheet("background-color: none")

        if self.CardReader.show_reset:
            self.ui.Reset_Credit_1.setText("Initialize")
            self.ui.Reset_Credit_2.setText("Initialize")
        else:
            self.ui.Reset_Credit_1.setText("Reset Page 1")
            self.ui.Reset_Credit_2.setText("Reset Page 2")

    def terminal(self):
        self.CardReader.run()


def trans_py_file(filename):
    return os.path.splitext(filename)[0] + '.py'


def convert_ui_to_py():
    py_file = trans_py_file(ui_file)

    if Path(py_file).exists():
        Path(py_file).unlink()
        print("Remove existing .py file")

    cmd = 'pyuic5 -o {py_file} {ui_file}'.format(py_file=py_file, ui_file=ui_file)
    print("Convert .ui file: " + ui_file)
    print("To .py file: " + py_file)

    os.system(cmd)


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    #convert_ui_to_py()
    from GUI import *

    main()
