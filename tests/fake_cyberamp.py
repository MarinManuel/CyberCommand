import os.path
import logging
import argparse
import random
import serial
import sys
import re

# FIXME: I don't know why we need this to load CyberAmp from the parent directory but this works...
directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# setting path
sys.path.append(directory)
# importing
# noinspection PyPep8Naming
import CyberAmp.CyberAmp as cyber


# noinspection SpellCheckingInspection
class FakeCyberAmp(cyber.CyberAmp):
    PREAMBLE = re.compile(r"^AT(?P<device>\d?)")
    RE_COUPLING = re.compile(r'C(?P<channel>\d)(?P<polarity>[+-])(?P<frequency>[013.]{1,3}|DC|GND)')
    RE_OFFSET = re.compile(r'D(?P<channel>\d)(?P<offset>[-+]\d+)')
    RE_LOWPASS = re.compile(r'F(?P<channel>\d)(?P<frequency>\d+|-)')
    RE_PREGAIN = re.compile(r'G(?P<channel>\d)P(?P<gain>\d+)')
    RE_POSTGAIN = re.compile(r'G(?P<channel>\d)O(?P<gain>\d+)')
    RE_NOTCH = re.compile(r'N(?P<channel>\d)(?P<notch>[-+])')
    RE_STATUS = re.compile(r'S(?P<channel>[+\d]?)')
    RE_AUTOZERO = re.compile(r'Z(?P<channel>\d)')
    RE_WRITE = re.compile(r'W')
    RE_DEFAULTS = re.compile(r'L')

    MAX_OFFSET = 5000000
    ANS_OOR = 'D{channel}=!'
    ANS_OFFSET = 'D{channel}={offset:+08d}'
    ANS = '\r>'

    SAVE_FILE = os.path.join(os.path.dirname(__file__), 'savefile')

    def __init__(self, device_id, serial=None, model_id='', rev_number='', serial_number=''):
        super(FakeCyberAmp, self).__init__(device_id, serial, model_id, rev_number, serial_number)
        self.commands = [
            (self.RE_COUPLING, self.process_coupling),
            (self.RE_OFFSET, self.process_offset),
            (self.RE_LOWPASS, self.process_lowpass),
            (self.RE_PREGAIN, self.process_pregain),
            (self.RE_POSTGAIN, self.process_postgain),
            (self.RE_NOTCH, self.process_notch),
            (self.RE_STATUS, self.process_status),
            (self.RE_AUTOZERO, self.process_autozero),
            (self.RE_WRITE, self.process_write),
            (self.RE_DEFAULTS, self.process_defaults)
        ]

    def parse_cmd(self, inLine):
        inLine = inLine.rstrip().upper()
        logging.debug(f'Received <{inLine}>')

        match = self.PREAMBLE.match(inLine)
        if match and (match.group('device') == '' or amp.device_id == int(match.group('device'))):
            for regex, func in self.commands:
                matches = regex.finditer(inLine)
                for match in matches:
                    logging.debug(f'Processing {match} with function {func}')
                    func(match)
        logging.info('Current configuration:')
        logging.info(self.print_status(include_channels=True))
        self.serial.write(self.ANS.encode())

    def process_coupling(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        if match.group('polarity') == '+':
            channel.pos_coupling = cyber.Coupling(match.group('frequency'))
        else:
            channel.neg_coupling = cyber.Coupling(match.group('frequency'))

    def process_offset(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        offset = int(match.group('offset'))
        if abs(offset) > self.MAX_OFFSET:
            self.serial.write(self.ANS_OOR.format(channel=channel.channel_number).encode())
        else:
            channel.offset = int(match.group('offset'))

    def process_lowpass(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        logging.debug(f'matched channel {channel}')
        channel.low_pass = cyber.LowPass(match.group('frequency'))

    def process_pregain(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        logging.debug(f'matched channel {channel}')
        channel.pre_gain = cyber.PreGain(match.group('gain'))

    def process_postgain(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        logging.debug(f'matched channel {channel}')
        channel.post_gain = cyber.PostGain(match.group('gain'))

    def process_notch(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        logging.debug(f'matched channel {channel}')
        channel.notch = cyber.Notch(match.group('notch'))

    def process_status(self, match):
        ch = match.group('channel')
        if ch == '' or ch == '0':
            logging.debug('Transmitting header only')
            self.serial.write(self.print_status(include_channels=False).encode())
        elif ch == '+':
            logging.debug('Transmitting full status')
            self.serial.write(self.print_status(include_channels=True).encode())
        else:
            channel = self.channels[int(ch) - 1]
            logging.debug(f'matched channel {channel}')
            self.serial.write(channel.print_status().encode())

    def process_autozero(self, match):
        channel = self.channels[int(match.group('channel')) - 1]
        logging.debug(f'matched channel {channel}')
        offset = int(random.uniform(-1., 1.) * 1e6)
        logging.debug(f'new offset is {offset:d}')
        self.serial.write(self.ANS_OFFSET.format(channel=channel.channel_number, offset=offset).encode())
        channel.offset = offset

    def process_write(self, match):
        logging.debug(f'Saving current configuration in file <{self.SAVE_FILE}>')
        with open(self.SAVE_FILE, 'w') as f:
            f.write('\n'.join([channel.print_status() for channel in self.channels]))

    def process_defaults(self, match):
        for channel in self.channels:
            channel.parse(f'{channel.channel_number} X=0        +=DC -=GND P=001 O=001 N=0 D=+0000000 F=10000')


logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help="Serial port to connect to")
    args = parser.parse_args()

    s = serial.Serial(args.port, timeout=0.1)
    amp = FakeCyberAmp(device_id=0, serial=s, model_id='380', rev_number='1.0.09', serial_number='#2460')
    # amp.channels[0].parse('1 X=ID1      +=DC  -=DC P=001 O=001 N=0 D=+0000010 F=10')
    # amp.channels[1].parse('2 X=ID2      +=GND -=DC P=010 O=002 N=1 D=+0000020 F=20')
    # amp.channels[2].parse('3 X=0        +=0.1 -=0.1 P=010 O=005 N=1 D=+0000030 F=30')
    if os.path.exists(FakeCyberAmp.SAVE_FILE):
        with open(FakeCyberAmp.SAVE_FILE, 'r') as f:
            for c, line in zip(amp.channels, f.readlines()):
                c.parse(line)

    logging.info(f'Listening on serial {s}')
    logging.info(f'Entering infinite loop. Press Ctrl+C to exit')
    try:
        while True:
            line = s.readline().decode('ascii')
            if len(line) > 0:
                amp.parse_cmd(line)

    except KeyboardInterrupt:
        pass
