import logging

from PyQt5.QtWidgets import QDialog, QGridLayout, QPushButton, QDialogButtonBox
import CyberAmp.CyberAmp


class TestDialog(QDialog):
    def __init__(self, cyberamp: CyberAmp.CyberAmp.CyberAmp):
        super(TestDialog, self).__init__()
        self.cyberamp = cyberamp
        self.electrodeTestButton = QPushButton(self)
        self.electrodeTestButton.setCheckable(True)
        self.electrodeTestButton.setText("&Electrode test")
        self.electrodeTestButton.setToolTip("Turn on/off 10 Hz electrode-test oscillator")

        self.notchTestButton = QPushButton(self)
        self.notchTestButton.setCheckable(True)
        self.notchTestButton.setText("&Notch filter test")
        self.notchTestButton.setToolTip("Turn on/off notch-filter test")

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)

        self.gridLayout = QGridLayout(self)
        self.gridLayout.addWidget(self.electrodeTestButton, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.notchTestButton, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.electrodeTestButton.clicked.connect(self.do_electrode_test)
        self.notchTestButton.clicked.connect(self.do_notch_test)
        self.buttonBox.accepted.connect(self.accept)

    def do_electrode_test(self, checked: bool):
        if checked and self.notchTestButton.isChecked():
            logging.debug("Notch test is running, stopping...")
            self.notchTestButton.setChecked(False)
        self.cyberamp.do_electrode_test(checked)

    def do_notch_test(self, checked: bool):
        if checked and self.electrodeTestButton.isChecked():
            logging.debug("Electrode test is running, stopping...")
            self.electrodeTestButton.setChecked(False)
        self.cyberamp.do_notch_test(checked)

    def accept(self):
        if self.electrodeTestButton.isChecked():
            logging.debug("Electrode test is still running. Stopping...")
            self.do_electrode_test(False)
        if self.notchTestButton.isChecked():
            logging.debug("Notch test is still running. Stopping...")
            self.do_notch_test(False)
        super(TestDialog, self).accept()
