from PyQt5 import QtWidgets
from pathlib import Path
from config import terminal_config
from terminal import *
from GUI import *

import sys
import os
import threading

class ApplicationWindow(QtWidgets.QMainWindow):
    closeApp = pyqtSignal()

    def __init__(self):
        self.name = 0
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_UpdateGUI()
        self.ui.setupUi(self)
        self.CardReader = Terminal()

        self.ui.value_1.setText(str(terminal_config["value_1"]) + " pro Kaffee")
        self.ui.value_service.setText(str(terminal_config["service"]))
        self.ui.value_1.clicked.connect(self.CardReader.setValue)
        self.ui.value_service.clicked.connect(self.CardReader.setValueService)
        self.ui.Reset_Credit_1.clicked.connect(self.CardReader.reset)
        self.ui.Update.valueChanged.connect(self.update_spin_roll)
        self.CardReader.UpdateUi.connect(self.update_ui)
        self.ui.UpdateButton.clicked.connect(self.CardReader.write_to_chip)
        t = threading.Thread(target=self.terminal)
        t.start()

    def update_spin_roll(self):
        self.CardReader.value = self.ui.Update.value()

    def closeEvent(self, event):
        event.accept()

    def update_ui(self):
        self.ui.UserID.setText("Card ID: " + str(self.CardReader.ActiveCardId))
        self.ui.Credit_1.setText(str(self.CardReader.ActiveCardCredit_1))
        self.ui.SystemOutput.setText(str(self.CardReader.system_output))

        if str(self.CardReader.system_output) == "Connection Active":
            self.ui.SystemOutput.setStyleSheet("background-color: green")
        elif str(self.CardReader.system_output) == "Hardware not found - connected?":
            self.ui.SystemOutput.setStyleSheet("background-color: red")
        else:
            self.ui.SystemOutput.setStyleSheet("background-color: none")

        if self.CardReader.show_reset:
            self.ui.Reset_Credit_1.setText("Initialize")
        else:
            self.ui.Reset_Credit_1.setText("Reset Page")

    def terminal(self):
        self.CardReader.run()

def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
