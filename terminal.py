import serial.tools.list_ports
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import *
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit
import sqlite3, os

import random
import time

reply_time = 0.1
unknown_txt = "unknown"
unknown_no = -1



# noinspection PyBroadException
class Terminal(QObject):
    SerialConnection = None
    is_running = False
    is_checking = True
    serial_reply = None
    system_output = ""
    activeID = "Unkown"
    write_to_chip_flag = False
    loopfinished = False
    ActiveCardId_old = None

    information_known = False

    card_is_present = False
    card_is_present_counter = 0

    ActiveCardCredit_1 = unknown_no
    ActiveCardCredit_2 = unknown_no
    ActiveCardId = unknown_txt
    ActiveCardIdName = unknown_txt

    hardware_connected = False

    UpdateUi = pyqtSignal()
    ResetPossible = pyqtSignal()
    ShowPopup = pyqtSignal()
    show_reset = False

    page_setting = 4
    credit_setting = 0.5
    service = False
    value = 0

    store = False
    saveSql = False
    connection = None
    cursor = None
    databaseclosed = False

    msg = None

    user_name = "???"

    @staticmethod
    def handle_serial_input(stream):
        return stream.replace(b"\r", b"").replace(b"\n", b"")

    def __init__(self):
        super(Terminal, self).__init__()

    def __del__(self):
        None
        #self.save_data_base()

    def save_data_base(self):
        print("Close connection")
        self.connection.close()
        self.databaseclosed = True

    def check_if_id_is_known(self, user_id):

        sql = "SELECT COUNT(*) FROM user WHERE id = %s" % user_id

        self.cursor.execute(sql)
        count = self.cursor.fetchone()[0]

        if count >= 1:
            return True
        else:
            return False

    def store_new_user(self, name):
        self.ActiveCardIdName = name
        self.store = True


    def sqlwrite(self):

        sql = "INSERT INTO user VALUES('%s', %s)" % (str(self.ActiveCardIdName), str(self.ActiveCardId))
        self.cursor.execute(sql)
        self.connection.commit()
        self.store = False


    def get_name_by_id(self, user_id):

        sql = "SELECT * FROM user WHERE id = %s" % user_id
        self.ActiveCardIdName = self.cursor.execute(sql).fetchone()[0]

        return self.ActiveCardIdName

    def output(self, txt):
        self.system_output = txt
        self.UpdateUi.emit()

    def setValue1(self):
        self.output("Set value to 50ct/unit")
        self.credit_setting = 0.5
        self.service = False

    def setValue2(self):
        self.output("Set value to 30ct/unit")
        self.credit_setting = 0.3
        self.service = False

    def setValueService(self):
        self.output("Set value to service")
        self.service = True

    def setPage1(self):
        self.output("Set active page to 5")
        self.page_setting = 5

    def setPage2(self):
        self.output("Set active page to 4")
        self.page_setting = 4

    def connect_to_hardware(self):
        ports = serial.tools.list_ports.comports()
        no_of_ports = len(ports)

        for port in ports:
            log = "Connect to: " + port.device
            self.output(log)

            try:
                self.SerialConnection = serial.Serial(ports[no_of_ports - 1].device, timeout=1, baudrate=115200)
                self.SerialConnection.flushInput()
                self.SerialConnection.flushOutput()
                self.SerialConnection.write(b'ping')
                time.sleep(reply_time)
                self.serial_reply = self.handle_serial_input(self.SerialConnection.readline())

                log = "Received: " + self.serial_reply
                self.output(log)

            except:
                log = "Can't connect to port: " + str(port)
                self.output(log)

            if self.serial_reply == b"pong":
                log = "Card reader found on port: " + port.device
                self.output(log)
                self.hardware_connected = True
                break

            no_of_ports -= 1

    def request_command(self, command):
        self.SerialConnection.flushOutput()
        self.SerialConnection.flushInput()
        self.SerialConnection.write(command)

    def handle_command(self, command):
        check = True
        counter = 0
        while check:
            self.request_command(b'ping')
            time.sleep(reply_time)
            self.serial_reply = self.handle_serial_input(self.SerialConnection.readline())

            if self.serial_reply == b'pong':
                self.output("Connection Active")
                self.request_command(command)
                time.sleep(reply_time)
                self.serial_reply = self.handle_serial_input(self.SerialConnection.readline())
                check = False
            else:
                time.sleep(1)
                counter += 1
                self.output("Synchronize serial connection and retry")
                if counter > 5:
                    self.output("Synchronize serial connection failed")
                    break

        return self.serial_reply

    def trigger_ui_update(self):
        self.UpdateUi.emit()

    def write_to_chip(self):

        self.is_checking = False
        self.output("Write new credit to chip")
        time.sleep(0.5)

        if self.service:
            credit = self.value
        else:
            if self.page_setting == 4:
                credit = int(self.ActiveCardCredit_2) + int(self.value / self.credit_setting)
            if self.page_setting == 5:
                credit = int(self.ActiveCardCredit_1) + int(self.value / self.credit_setting)

        cmd = (str(self.page_setting) + "_WriteCredit_" + str(credit)).encode('utf-8')
        counter = 0

        while True:

            self.serial_reply = self.handle_command(cmd)
            self.output(self.serial_reply)

            if str(self.serial_reply).endswith("_0'"):
                self.output("Write OK!")
                self.is_checking = True
                return True
            else:
                self.output("Writing to card...")
                counter += 1

            if counter >= 5:
                self.output("Write not OK!")
                self.is_checking = True
                return False

    def reset_1(self):
        self.is_checking = False

        if self.show_reset:
            self.output("Initialize unkown chip")
            self.card_init()
            return

        self.output("Reset Page 1")
        time.sleep(0.5)

        counter = 0

        while True:

            self.serial_reply = self.handle_command(b'5_Reset')
            self.output(self.serial_reply)

            if str(self.serial_reply).endswith("_0'"):
                self.output("Write OK!")
                self.is_checking = True
                return True
            else:
                self.output("Writing to card...")
                counter += 1

            if counter >= 5:
                self.output("Write not OK!")
                self.is_checking = True
                return False

    def reset_2(self):
        self.is_checking = False

        if self.show_reset:
            self.output("Initialize unkown chip")
            self.card_init()
            return

        self.output("Reset Page 2")
        time.sleep(0.5)

        counter = 0

        while True:

            self.serial_reply = self.handle_command(b'4_Reset')
            self.output(self.serial_reply)

            if str(self.serial_reply).endswith("_0'"):
                self.output("Write OK!")
                self.is_checking = True
                return True
            else:
                self.output("Writing to card...")
                counter += 1

            if counter >= 5:
                self.output("Write not OK!")
                self.is_checking = True
                return False

    def card_init(self):
        self.is_checking = False
        time.sleep(0.5)
        self.serial_reply = self.handle_command(b'Init')
        print(self.serial_reply)
        self.is_checking = True

    def run(self):

        self.connect_to_hardware()

        self.connection = sqlite3.connect("user.db")
        self.cursor = self.connection.cursor()

        if self.hardware_connected:
            self.is_running = True
        else:
            self.output("Hardware not found - connected?")

        while self.is_running:
            if self.is_checking:
                self.loopfinished = False
                if self.handle_command(b'IsNewCardPresent'):
                    information = str(self.handle_command(b'GetCardInformation'))
                    information = information.replace('b', "").replace('\'', "")
                    split_information = information.split("_")
                    if len(split_information) != 3 or information.startswith("0_"):
                        continue
                    self.ActiveCardId = split_information[0]

                    if self.check_if_id_is_known(str(self.ActiveCardId)):
                        self.user_name = self.get_name_by_id(str(self.ActiveCardId))
                    else:
                        if self.ActiveCardId != self.ActiveCardId_old:
                            self.ShowPopup.emit()
                            self.ActiveCardId_old = self.ActiveCardId

                    self.ActiveCardCredit_1 = split_information[1]
                    self.ActiveCardCredit_2 = split_information[2]

                    if int(self.ActiveCardCredit_1) == -1 and int(self.ActiveCardCredit_2) == -1:
                        self.show_reset = True
                    else:
                        self.show_reset = False

                    if self.store:
                        self.sqlwrite()

                    self.UpdateUi.emit()
                self.loopfinished = True

            time.sleep(0.1)
