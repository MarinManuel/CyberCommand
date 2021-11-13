import logging
import re
from enum import Enum

NB_DEVICES = 10
NB_CHANNELS = 8
MAX_BAUDRATE = 19200
END_TRANSMIT = '>'.encode()
TIMEOUT = 0.5


class Coupling(Enum):
    GND = 'GND'
    DC = 'DC'
    HP01 = '0.1'
    HP1 = '1'
    HP10 = '10'
    HP30 = '30'
    HP100 = '100'
    HP300 = '300'


# noinspection SpellCheckingInspection
class LowPass(Enum):
    LPBYPASS = '-'
    LP2 = '2'
    LP4 = '4'
    LP6 = '6'
    LP8 = '8'
    LP10 = '10'
    LP12 = '12'
    LP14 = '14'
    LP16 = '16'
    LP18 = '18'
    LP20 = '20'
    LP22 = '22'
    LP24 = '24'
    LP26 = '26'
    LP28 = '28'
    LP30 = '30'
    LP40 = '40'
    LP60 = '60'
    LP80 = '80'
    LP100 = '100'
    LP120 = '120'
    LP140 = '140'
    LP160 = '160'
    LP180 = '180'
    LP200 = '200'
    LP220 = '220'
    LP240 = '240'
    LP260 = '260'
    LP280 = '280'
    LP300 = '300'
    LP400 = '400'
    LP600 = '600'
    LP800 = '800'
    LP1000 = '1000'
    LP1200 = '1200'
    LP1400 = '1400'
    LP1600 = '1600'
    LP1800 = '1800'
    LP2000 = '2000'
    LP2200 = '2200'
    LP2400 = '2400'
    LP2600 = '2600'
    LP2800 = '2800'
    LP3000 = '3000'
    LP4000 = '4000'
    LP6000 = '6000'
    LP8000 = '8000'
    LP10000 = '10000'
    LP12000 = '12000'
    LP14000 = '14000'
    LP16000 = '16000'
    LP18000 = '18000'
    LP20000 = '20000'
    LP22000 = '22000'
    LP24000 = '24000'
    LP26000 = '26000'
    LP28000 = '28000'
    LP30000 = '30000'


class PreGain(Enum):
    P1 = '1'
    P10 = '10'
    P100 = '100'


class PostGain(Enum):
    O1 = '1'
    O2 = '2'
    O5 = '5'
    O10 = '10'
    O20 = '20'
    O50 = '50'
    O100 = '100'
    O200 = '200'


class Notch(Enum):
    ON = '+'
    OFF = '-'


class Input(Enum):
    POS = '+'
    NEG = '-'


class Channel:
    parse_regex = re.compile(r'''^
(?P<chan_num>[1-8])\s+                  # Channel Number 
X=(?P<probe_id>[\d\w]{1,8})\s+          # Probe ID. At most 8 alphanumerical char 
\+=(?P<pos_coupling>[\d.]+|GND|DC)\s+   # Positive input coupling. 
                                        # One of GND DC 0.1 1 10 30 100 300
-=(?P<neg_coupling>[\d.]+|GND|DC)\s+    # Negative input coupling. 
                                        # One of GND DC 0.1 1 10 30 100 300
P=(?P<pre_gain>\d+)\s+                  # Pre-amplifier gain. One of 1, 10 or 100
O=(?P<post_gain>\d+)\s+                 # Post-amplifier gain. 
                                        # One of 1, 2, 5, 10, 20, 50, 100 or 200
N=(?P<notch>[01])\s+                    # Notch filter. Either 0 or 1
D=(?P<offset>[+-]\d+)\s+                # Input offset.
F=(?P<low_pass>\d+|-)                     # Low pass filter frequency
$''', flags=re.VERBOSE)

    def __init__(self, num):
        self.channel_number = num
        self.probe_id = ''
        self.pos_coupling = Coupling.GND
        self.neg_coupling = Coupling.GND
        self.low_pass = LowPass.LP10000
        self.pre_gain = PreGain.P1
        self.post_gain = PostGain.O1
        self.notch = Notch.OFF
        self.offset = int()  # in micro-volts

    @staticmethod
    def strip_zeros(inStr):
        """
        Strips leading zeros from a string. Handles two special cases:
         - if string is constituted only of zeros ('0' or '00', etc) then returns '0'
         - if string contains a decimal point, then leaves the first zero
        :param inStr: string to be processed
        :return: string without leading zeros
        """
        if len(inStr) == 0:
            return ''

        s = inStr.lstrip('0')
        if len(s) == 0:
            s = '0'
        if s.startswith('.'):
            s = '0' + s
        return s

    def parse(self, config_string):
        """
        Parse the response of the CyberAmp and adjust the internal state of the channel accordingly
        :param config_string: the string returned by the CyberAmp. Format:
            3 X=AI334 +=DC -=030 P=010 O=002 N=1 D=-0123450 F=40
        """
        match = self.parse_regex.match(config_string)
        if not match:
            raise ValueError('Failed to parse string ' + config_string)
        # noinspection SpellCheckingInspection
        if self.channel_number != int(match.group('chan_num')):
            raise ValueError(f'String <{config_string}> does not match channel number <{self.channel_number}>')

        self.probe_id = match.group('probe_id')
        if self.probe_id == '0':
            self.probe_id = ''
        self.pos_coupling = Coupling(self.strip_zeros(match.group('pos_coupling')))
        self.neg_coupling = Coupling(self.strip_zeros(match.group('neg_coupling')))
        self.pre_gain = PreGain(self.strip_zeros(match.group('pre_gain')))
        self.post_gain = PostGain(self.strip_zeros(match.group('post_gain')))
        self.notch = Notch.ON if match.group('notch') == '1' else Notch.OFF
        self.offset = int(match.group('offset'))
        self.low_pass = LowPass(self.strip_zeros(match.group('low_pass')))

    def __repr__(self):
        return f'{self.__class__.__name__} at {str(hex(id(self)))} <' + \
               '; '.join([f'{k}: {v}' for k, v in self.__dict__.items()]) + \
               '>'

    def print_status(self):
        return f'{self.channel_number:d} X={"0" if len(self.probe_id) == 0 else self.probe_id:<8s} ' + \
               f'+={self.pos_coupling.value:<3s} -={self.neg_coupling.value:<3s} P={self.pre_gain.value:>03s} ' + \
               f'O={self.post_gain.value:>03s} N={"1" if self.notch == Notch.ON else "0"} D={self.offset:+08d} ' + \
               f'F={self.low_pass.value}'


class CyberAmp(object):
    PREAMBLE = 'AT{device_id}'
    CMD_STATUS = 'S+'
    CMD_WRITE = 'W'
    CMD_DEFAULTS = 'L'
    CMD_COUPLING = 'C{channel}{polarity}{coupling}'
    CMD_OFFSET = 'D{channel}{offset:+08d}'
    CMD_LOWPASS = 'F{channel}{frequency}'
    CMD_PREGAIN = 'G{channel}P{gain}'
    CMD_POSTGAIN = 'G{channel}O{gain}'
    CMD_NOTCH = 'N{channel}{notch}'
    CMD_ZERO = 'Z{channel}'
    CMD_ELECTRODE_TEST = 'TO{state}'
    CMD_NOTCH_TEST = 'TN{state}'

    # noinspection SpellCheckingInspection
    STATUS_REGEX = r'''(?P<model>CYBERAMP \d+) REV (?P<rev_number>[\d.]+)\s+SERIAL (?P<serial>[#\d]+)'''
    regex_status = re.compile(STATUS_REGEX, flags=re.MULTILINE)

    OFFSET_REGEX = r'''^D(?P<channel>\d)=(?P<offset>[+-]\d+)'''
    regex_offset = re.compile(OFFSET_REGEX, flags=re.MULTILINE)

    def __init__(self, device_id, serial=None, model_id='', rev_number='', serial_number=''):
        self.device_id = device_id
        self.serial = serial  # Serial(serial=serial, baudrate=baudrate)
        self.channels = [Channel(i + 1) for i in range(NB_CHANNELS)]
        self.model_id = model_id
        self.rev_number = rev_number
        self.serial_number = serial_number

    def send_command(self, command):
        self.serial.timeout = TIMEOUT
        cmd = self.PREAMBLE.format(device_id=self.device_id)
        cmd += command
        cmd += '\r\n'
        logging.debug(f'Sending command to CyberAmp: {cmd}')
        self.serial.write(cmd.encode())
        ret = self.serial.read_until(END_TRANSMIT).decode('ascii')
        log_ret = ret.replace('\r', '\n')
        logging.debug(f'Received response : {log_ret}')
        return ret

    def refresh(self):
        out = self.send_command(self.CMD_STATUS.format(device_id=self.device_id))
        logging.debug(f'Current status is:')
        logging.debug(out.replace('\r', '\n'))
        self.parse_status(out)

    def parse_status(self, out):
        match = self.regex_status.match(out)
        if not match:
            raise ValueError(f'ERROR parsing status from CyberAmp, answer was <{out}>')

        self.model_id = match.group('model')
        self.rev_number = match.group('rev_number')
        self.serial_number = match.group('serial')
        params = out[match.end() + 1:].splitlines()
        for channel, line in zip(self.channels, params):
            channel.parse(line)

    @staticmethod
    def validate_channel(channel):
        if channel < 1 or channel > NB_CHANNELS:
            raise ValueError(f'ERROR: channel <{channel}> must be in the range [1-{NB_CHANNELS}]')
        return channel

    def set_params(self, channel: int,
                   pos_coupling: Coupling = None, neg_coupling: Coupling = None,
                   pre_gain: PreGain = None, post_gain: PostGain = None, low_pass: LowPass = None,
                   notch: Notch = None):
        """
        Set all (or a subset of) channel parameters in one command
        :param channel: channel number (1-8)
        :param pos_coupling: Coupling for positive input
        :param neg_coupling: Coupling for negative input
        :param pre_gain: Pre-amplifier gain
        :param post_gain: Post-amplifier gain
        :param low_pass: Low-pass filter frequency
        :param notch: Whether to include a notch filter
        """
        channel = self.validate_channel(channel)
        cmd = ''
        if pos_coupling is not None:
            cmd += self.CMD_COUPLING.format(channel=channel, polarity='+', coupling=pos_coupling.value) + ' '
        if neg_coupling is not None:
            cmd += self.CMD_COUPLING.format(channel=channel, polarity='-', coupling=neg_coupling.value) + ' '
        if pre_gain is not None:
            cmd += self.CMD_PREGAIN.format(channel=channel, gain=pre_gain.value) + ' '
        if post_gain is not None:
            cmd += self.CMD_POSTGAIN.format(channel=channel, gain=post_gain.value) + ' '
        if low_pass is not None:
            cmd += self.CMD_LOWPASS.format(channel=channel, frequency=low_pass.value) + ' '
        if notch is not None:
            cmd += self.CMD_NOTCH.format(channel=channel, notch=notch.value) + ' '

        if len(cmd) > 0:
            self.send_command(cmd)

    def set_offset(self, channel: int, offset: int):
        """
        set DC offset in micro-volts
        :param channel: channel number (1-8)
        :param offset: offset in micro-volts (+/-7 digits)
        """
        out = self.send_command(self.CMD_OFFSET.format(channel=self.validate_channel(channel),
                                                       offset=offset))
        if '!' in out:
            raise ValueError(f'ERROR: Offset <{offset:+08d}> is out of range')
        else:
            self.channels[channel - 1].offset = offset

    def do_autozero(self, channel: int):
        """
        This command automatically zeros out the DC content of the input signal and reports the level.
        :param channel: channel number (1-8)
        """
        out = self.send_command(self.CMD_ZERO.format(channel=self.validate_channel(channel)))
        if '!' in out:
            raise ValueError(f'ERROR: Signal is out of range, or channel is faulty')
        else:
            match = self.regex_offset.match(out)
            if not match:
                raise ValueError(f'ERROR parsing response <{out}>')
        self.channels[channel - 1].offset = int(match.group('offset'))

    def print_status(self, include_channels=True):
        # noinspection SpellCheckingInspection
        out = f'CYBERAMP {self.model_id} REV {self.rev_number}\nSERIAL {self.serial_number}\n'
        if include_channels:
            for channel in self.channels:
                out += channel.print_status() + '\n'
        return out

    def do_write(self):
        self.send_command(self.CMD_WRITE)

    def load_defaults(self):
        self.send_command(self.CMD_DEFAULTS)
        self.refresh()

    def do_electrode_test(self, on: bool):
        self.send_command(self.CMD_ELECTRODE_TEST.format(state='+' if on else '-'))

    def do_notch_test(self, on: bool):
        self.send_command(self.CMD_NOTCH_TEST.format(state='+' if on else '-'))
