import re

from serial import Serial
from enum import Enum


class Coupling(Enum):
    GND = 'GND'
    DC = 'DC'
    HP01 = '0.1'
    HP1 = '1'
    HP10 = '10'
    HP30 = '30'
    HP100 = '100'
    HP300 = '300'


class LowPass(Enum):
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


class Channel:
    parse_regex = re.compile(r'''^
                                 (?P<chan_num>[1-8])\s+                  # Channel Number 
                                 X=(?P<probe_id>[\d\w]{1,8})\s+          # Probe ID. At most 8 alphanumerical char 
                                 \+=(?P<pos_coupling>[\d\.]+|GND|DC)\s+  # Positive input coupling. One of GND DC 0.1 1 10 30 100 300
                                 \-=(?P<neg_coupling>[\d\.]+|GND|DC)\s+  # Negative input coupling. One of GND DC 0.1 1 10 30 100 300
                                 P=(?P<pre_gain>\d+)\s+                  # Pre-amplifier gain. One of 1, 10 or 100
                                 O=(?P<post_gain>\d+)\s+                 # Post-amplifier gain. One of 1, 2, 5, 10, 20, 50, 100 or 200
                                 N=(?P<notch>[01])\s+                    # Notch filter. Either 0 or 1
                                 D=(?P<offset>[+-]\d+)\s+                # Input offset.
                                 F=(?P<low_pass>\d+)                     # Low pass filter frequency
                                 $'''
                             , flags=re.VERBOSE)

    def __init__(self, num):
        self.channel_number = num
        self.probe_id = ''
        self.pos_coupling = Coupling.GND
        self.neg_coupling = Coupling.GND
        self.low_pass = LowPass.LP10000
        self.pre_gain = PreGain.P1
        self.post_gain = PostGain.O1
        self.notch = Notch.OFF
        self.offset = 0.

    @staticmethod
    def strip_zeros(inStr):
        """
        Strips leading zeros from a string. Handles two special cases:
         - if string is constituted only of zeros ('0' or '00', etc) then returns '0'
         - if string contains a decimal point, then leaves the first zero
        :param inStr: string to be processed
        :return: string without leading zeros
        """
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
        self.offset = float(match.group('offset'))
        self.low_pass = LowPass(self.strip_zeros(match.group('low_pass')))

    def __repr__(self):
        return f'{self.__class__.__name__} at {str(hex(id(self)))} <' + \
               '; '.join([f'{k}: {v}' for k, v in self.__dict__.items()]) + \
               '>'


class CyberAmp(object):
    def __init__(self, port=None, baudrate=19200):
        serial = Serial(port=port, baudrate=baudrate)
        channels = [Channel(i + 1) for i in range(8)]
