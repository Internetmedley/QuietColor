import pyaudio
import numpy as np
from scipy.signal import bilinear
from scipy.signal import lfilter
from gpiozero import *
import time
import json


GREEN = LED(4)
YELLOW = LED(17)
RED = LED(27)
new_decibel = 0
tot_decibel = 0
gem_decibel = 0
time_decibel = 0
CHUNK = 256
RATE = 48000
form_1 = pyaudio.paInt16 # 16-bit resolution
CHAN = 1 # 1 channel
DEV_INDEX = 2 # device index found by p.get_device_info_by_index(ii)
loops = 0
avgList = []

p = pyaudio.PyAudio()

# input stream setup
stream = p.open(format = form_1, rate = RATE, channels = CHAN, \
                input_device_index = DEV_INDEX, input = True, \
                frames_per_buffer=CHUNK)


def A_weighting(fs):
    """Design of an A-weighting filter.
    b, a = A_weighting(fs) designs a digital A-weighting filter for
    sampling frequency `fs`. Usage: y = scipy.signal.lfilter(b, a, x).
    Warning: `fs` should normally be higher than 20 kHz. For example,
    fs = 48000 yields a class 1-compliant filter.
    References:
       [1] IEC/CD 1672: Electroacoustics-Sound Level Meters, Nov. 1996.
    """
    # Definition of analog A-weighting filter according to IEC/CD 1672.
    f1 = 20.598997
    f2 = 107.65265
    f3 = 737.86223
    f4 = 12194.217
    A1000 = 1.9997

    NUMs = [(2*np.pi * f4)**2 * (10**(A1000/20)), 0, 0, 0, 0]
    DENs = np.polymul([1, 4*np.pi * f4, (2*np.pi * f4)**2],
                   [1, 4*np.pi * f1, (2*np.pi * f1)**2])
    DENs = np.polymul(np.polymul(DENs, [1, 2*np.pi * f3]),
                                 [1, 2*np.pi * f2])

    # Use the bilinear transformation to get the digital filter.
    # (Octave, MATLAB, and PyLab disagree about Fs vs 1/Fs)
    return bilinear(NUMs, DENs, fs)

NUMERATOR, DENOMINATOR = A_weighting(RATE)

def rms_flat(a):  # from matplotlib.mlab
    """
    Return the root mean square of all the elements of *a*, flattened out.
    """
    return np.sqrt(np.absolute(np.mean(np.absolute(a)**2)))




# while True:  # Used to continuously stream audio
while True:
    with open('/var/www/html/data/data.json', 'r') as f:
        raw_json = json.load(f)

    decoded_block = np.fromstring(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    y = lfilter(NUMERATOR, DENOMINATOR, decoded_block)
    new_decibel = 20 * np.log10(rms_ flat(y))
    raw_json["1"]["decibel"] = gem_decibel
    tot_decibel = tot_decibel + new_decibel
    time_decibel = time_decibel + 0.075

    if time_decibel > 5:
        gem_decibel = tot_decibel / 67
        print("Gemiddelde decibel: {}".format(gem_decibel))
        if gem_decibel >= int(raw_json["1"]["max_decibel"]):
            RED.on()
            YELLOW.on()
            GREEN.on()
        elif gem_decibel >= int(raw_json["1"]["medium_decibel"]) and gem_decibel < int(raw_json["1"]["max_decibel"]):
            RED.off()
            YELLOW.on()
            GREEN.on()
        else:
            RED.off()
            YELLOW.off()
            GREEN.on()
        time_decibel = 0
        tot_decibel = 0

    with open('/var/www/html/data/data.json', 'w') as f:
        json.dump(raw_json, f)20

    time.sleep(0.075)

# stop met audio streamen
stream.stop_stream()
stream.close()
p.terminate
