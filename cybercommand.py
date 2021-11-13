import argparse
import itertools
import logging
import serial
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QInputDialog, QMainWindow, QTabWidget, QWidget, QComboBox, QDoubleSpinBox, \
    QToolButton, QCheckBox, QLabel, QAction
from serial.tools import list_ports
from CyberAmp import CyberAmp
from tqdm import tqdm

DEFAULT_BAUDRATE = CyberAmp.MAX_BAUDRATE


def discover_addresses(port, baudrate=DEFAULT_BAUDRATE):
    """
    discover the valid devices ids on the given serial serial
    :param port:  serial serial to connect to
    :param baudrate: baudrate
    :return: a list of valid addresses, or an empty list
    """
    valid_ids = []
    s = serial.Serial(port=port, baudrate=baudrate, timeout=CyberAmp.TIMEOUT)
    for id_ in tqdm(range(CyberAmp.NB_DEVICES), desc='scanning for devices'):
        s.write(f'AT{id_}S\r'.encode())
        out = s.read_until(CyberAmp.END_TRANSMIT).decode('ascii')
        # noinspection SpellCheckingInspection
        if 'CYBERAMP' in out:
            valid_ids.append(id_)
    s.close()
    return valid_ids


def discover_devices(port=None, baudrate=DEFAULT_BAUDRATE):
    """
    scan through the available serial ports and return a list of
    ports to which a CyberAmp is connected
    :param port: if not None, scan only that serial serial,
                 otherwise, scans all available serial ports
    :param baudrate: baudrate
    :return: a list of tuples.
             The first element of each tuple is the serial serial,
             the second is a list of device addresses
    """
    if port is None:
        serial_ports = [d.device for d in list_ports.comports()]
    else:
        serial_ports = [port]
    valid_ports = []
    # try to connect to each serial ports, and test if CyberAmp responds
    for port in tqdm(serial_ports, desc='scanning serial ports'):
        # noinspection PyBroadException
        try:
            s = serial.Serial(port=port, baudrate=baudrate, timeout=CyberAmp.TIMEOUT)
            s.write('ATS\r'.encode())
            out = s.read_until(CyberAmp.END_TRANSMIT).decode('ascii')
            s.close()
            # noinspection SpellCheckingInspection
            if 'CYBERAMP' in out:
                found_ids = discover_addresses(port=port, baudrate=baudrate)
                valid_ports.extend(itertools.product([port], found_ids))
        except Exception as e:
            logging.debug("Encountered Exception: " + str(e))
            pass
    return valid_ports


class CyberWindow(QMainWindow):
    tabWidget: QTabWidget
    posCouplingComboBox: QComboBox
    negCouplingComboBox: QComboBox
    offsetSpinBox: QDoubleSpinBox
    autoOffsetButton: QToolButton
    preGainComboBox: QComboBox
    postGainComboBox: QComboBox
    lowPassComboBox: QComboBox
    notchCheckBox: QCheckBox
    actionWrite: QAction
    actionQuit: QAction
    actionDefaults: QAction
    actionOscillators: QAction
    actionTerminal: QAction
    offsetStyleError = 'background: red'

    def __init__(self, cyberamp: CyberAmp):
        super(CyberWindow, self).__init__()
        uic.loadUi('MainWindow.ui', self)  # Load the .ui file
        self.cyberamp = cyberamp

        self.probeIdLabel = QLabel()
        self.statusBar().addWidget(self.probeIdLabel)

        # create necessary amount of tabs
        for i, channel in enumerate(self.cyberamp.channels):
            self.tabWidget.addTab(QWidget(), f'Channel {i + 1:d}')
        self.tabWidget.setCurrentIndex(0)  # select first tab

        # populate the content of the widgets
        self.posCouplingComboBox.clear()
        self.posCouplingComboBox.addItems([a.value for a in CyberAmp.Coupling])
        self.negCouplingComboBox.clear()
        self.negCouplingComboBox.addItems([a.value for a in CyberAmp.Coupling])
        self.preGainComboBox.clear()
        self.preGainComboBox.addItems([a.value for a in CyberAmp.PreGain])
        self.postGainComboBox.clear()
        self.postGainComboBox.addItems([a.value for a in CyberAmp.PostGain])
        self.lowPassComboBox.clear()
        self.lowPassComboBox.addItems([a.value for a in CyberAmp.LowPass])

        # Signals
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.posCouplingComboBox.currentIndexChanged.connect(self.update_channel)
        self.negCouplingComboBox.currentIndexChanged.connect(self.update_channel)
        self.preGainComboBox.currentIndexChanged.connect(self.update_channel)
        self.postGainComboBox.currentIndexChanged.connect(self.update_channel)
        self.lowPassComboBox.currentIndexChanged.connect(self.update_channel)
        self.notchCheckBox.stateChanged.connect(self.update_channel)
        self.offsetSpinBox.valueChanged.connect(self.set_offset)
        self.autoOffsetButton.clicked.connect(self.do_autozero)
        self.actionWrite.triggered.connect(self.cyberamp.do_write)
        self.actionQuit.triggered.connect(self.close)
        self.actionDefaults.triggered.connect(self.load_defaults)

        self.refresh()
        self.show()

    def refresh(self):
        self.cyberamp.refresh()
        channel = self.cyberamp.channels[self.tabWidget.currentIndex()]

        self.do_block_signals(True)

        i = self.posCouplingComboBox.findText(channel.pos_coupling.value)
        self.posCouplingComboBox.setCurrentIndex(i)

        i = self.negCouplingComboBox.findText(channel.neg_coupling.value)
        self.negCouplingComboBox.setCurrentIndex(i)

        self.offsetSpinBox.setValue(channel.offset * 1e-6)

        i = self.preGainComboBox.findText(channel.pre_gain.value)
        self.preGainComboBox.setCurrentIndex(i)

        i = self.postGainComboBox.findText(channel.post_gain.value)
        self.postGainComboBox.setCurrentIndex(i)

        i = self.lowPassComboBox.findText(channel.low_pass.value)
        self.lowPassComboBox.setCurrentIndex(i)

        self.notchCheckBox.setChecked(channel.notch == CyberAmp.Notch.ON)

        self.probeIdLabel.setText(f'Probe ID: {channel.probe_id}')

        self.do_block_signals(False)

    def do_block_signals(self, block):
        self.posCouplingComboBox.blockSignals(block)
        self.negCouplingComboBox.blockSignals(block)
        self.offsetSpinBox.blockSignals(block)
        self.preGainComboBox.blockSignals(block)
        self.postGainComboBox.blockSignals(block)
        self.lowPassComboBox.blockSignals(block)
        self.notchCheckBox.blockSignals(block)

    def tabChanged(self, _):
        self.refresh()

    # noinspection PyUnusedLocal
    def update_channel(self, *args, **kwargs):
        channel = self.tabWidget.currentIndex()+1
        pos_coupling = CyberAmp.Coupling(self.posCouplingComboBox.currentText())
        neg_coupling = CyberAmp.Coupling(self.negCouplingComboBox.currentText())
        pre_gain = CyberAmp.PreGain(self.preGainComboBox.currentText())
        post_gain = CyberAmp.PostGain(self.postGainComboBox.currentText())
        low_pass = CyberAmp.LowPass(self.lowPassComboBox.currentText())
        notch = CyberAmp.Notch.ON if self.notchCheckBox.isChecked() else CyberAmp.Notch.OFF
        self.cyberamp.set_params(channel=channel, pos_coupling=pos_coupling, neg_coupling=neg_coupling,
                                 pre_gain=pre_gain, post_gain=post_gain, low_pass=low_pass, notch=notch)
        self.refresh()

    def set_offset(self, value):
        channel = self.cyberamp.channels[self.tabWidget.currentIndex()]
        old_offset = channel.offset
        new_offset = int(value * 1e6)
        try:
            self.cyberamp.set_offset(channel.channel_number, new_offset)
            self.offsetSpinBox.setStyleSheet('')
        except ValueError:
            self.offsetSpinBox.blockSignals(True)
            self.offsetSpinBox.setValue(old_offset * 1e-6)
            self.offsetSpinBox.setStyleSheet(self.offsetStyleError)
            self.offsetSpinBox.setFocus()
            self.statusBar().showMessage("Offset is out of range!", msecs=2000)
            self.offsetSpinBox.blockSignals(False)
        self.refresh()

    def do_autozero(self, _):
        channel = self.tabWidget.currentIndex()+1
        self.cyberamp.do_autozero(channel)
        self.refresh()

    def load_defaults(self, _):
        self.cyberamp.load_defaults()
        self.refresh()


if __name__ == '__main__':
    # Create the application
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help="Serial port to connect to"
                                       "(if not supplied, automatically search for valid ports)")
    parser.add_argument('--baudrate', help='Serial communication speed', default=DEFAULT_BAUDRATE)
    parser.add_argument('--device', help='Device address [0-9]'
                                         '(if not supplied, automatically search for valid address)')
    parser.add_argument('--log-level', help='level of information to print to stdout'
                                            'Can be one of [DEBUG,INFO,WARNING,ERROR,CRITICAL]. '
                                            'Default is WARNING',
                        default='WARNING')
    cli_arguments = parser.parse_args()

    logging.basicConfig(level=getattr(logging, cli_arguments.log_level.upper()))

    # This part is used for auto discovery of the CyberAmp(s) connected to the computer
    # If the user has provided a serial and/or a device address, then we use that, and
    # the list `devices` contains only one element [(serial, [address])]
    # if either of those are missing, then we scan through all the ports and all the
    # possible addresses, and the list `devices` may contain more than one element
    # e.g. devices = [('COM1', 0), ('/dev/ttyUSB0', 1), ('/dev/ttyUSB0', 9)]
    devices = []
    if cli_arguments.port is not None and cli_arguments.device is not None:
        devices = [(cli_arguments.port, cli_arguments.device)]
    else:
        devices = discover_devices(port=cli_arguments.port, baudrate=cli_arguments.baudrate)
    logging.debug('Devices found: ' + str(devices))

    if len(devices) == 0:
        raise RuntimeError('ERROR: cannot find an appropriate serial serial. Aborting')

    # if we found more than one device (on one or more serial serial),
    # then we show a dialog box to let the user choose which one they want to use
    # We have to convert a list with possible sub-lists of variable length into a
    # 1D list with human readable content, and then match back the choice that the user made
    # with the right info.
    if len(devices) > 1:
        readable_devices = ['Port {} (address {})'.format(*d) for d in devices]
        # noinspection PyTypeChecker
        choice, ok = QInputDialog.getItem(None, "Select device", 'Device', readable_devices)
        if not ok:
            sys.exit(0)
        devices = [devices[readable_devices.index(choice)]]

    # at this point `devices` should contain a single tuple [(serial, address)]
    logging.debug('Devices found after user query: ' + str(devices))
    serial_port, device_id = devices[0]

    serial_obj = serial.Serial(port=serial_port, baudrate=cli_arguments.baudrate)
    amp = CyberAmp.CyberAmp(device_id=device_id, serial=serial_obj)
    logging.info(f"Connected to serial <{serial_port}>, address <{device_id}>: {amp.__repr__()}")
    amp.refresh()
    print(amp.print_status(include_channels=True))

    mainWindow = CyberWindow(cyberamp=amp)

    # Run the application's main loop
    sys.exit(app.exec())
