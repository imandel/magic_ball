from flask import Flask, Response,render_template
from flask_socketio import SocketIO, send, emit
import pyaudio

import time
import board
import busio
import adafruit_mpu6050
import json

import signal
import sys
from queue import Queue

from engineio.payload import Payload

Payload.max_decode_packets = 50
 
i2c = busio.I2C(board.SCL, board.SDA)
mpu = adafruit_mpu6050.MPU6050(i2c)

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 1024
# RECORD_SECONDS = 0.5
bitsPerSample = 16

audioBuffer = Queue()

audio1 = pyaudio.PyAudio()

app = Flask(__name__)
socketio = SocketIO(app)

for ii in range(audio1.get_device_count()):
    print(audio1.get_device_info_by_index(ii).get('name'))

def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

first_packet = True
loaded = False
wav_header = genHeader(RATE, bitsPerSample, CHANNELS)

def callback(in_data, frame_count, time_info, flag):
    if loaded:
        audioBuffer.put(in_data)
    return (None, pyaudio.paContinue)

# create pyaudio stream
stream = audio1.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,input_device_index=2,
                frames_per_buffer=CHUNK, stream_callback=callback)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    stream.stop_stream()
    stream.close()
    audio1.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("recording")


@app.route('/audio')
def audio():
    def sound():
        global first_packet
        global loaded
        loaded = True
        while True:
            try:
                data = audioBuffer.get(True)
                if data is None:
                    continue
                if first_packet:
                    wav_header = genHeader(RATE, bitsPerSample, CHANNELS)

                    data = wav_header + audioBuffer.get(True)
                    first_packet = False
                else:
                    data = audioBuffer.get(True)
                # print(data)
            except queue.Empty:
                continue
            print(time.time(), len(data))
            yield data
    # # start Recording
    # def sound():

        # CHUNK = 4096
        # sampleRate = 44100
        # bitsPerSample = 16
        # channels = 1
        # wav_header = genHeader(sampleRate, bitsPerSample, channels)

    #     stream = audio1.open(format=FORMAT, channels=CHANNELS,
    #                     rate=RATE, input=True,input_device_index=2,
    #                     frames_per_buffer=CHUNK)
    #     print("recording...")
    #     first_run = True
    #     while True:
    #        if first_run:
    #            data = wav_header + stream.read(CHUNK)
    #            first_run = False
    #        else:
    #            data = stream.read(CHUNK, exception_on_overflow = False)
    #        print(data)
    #        yield(data)

    return Response(sound())

# @socketio.on('connect')
# def test_connect():
#     print('connected')
#     emit('after connect',  {'data':'Lets dance'})

# @socketio.on('ping')
# def handle_message(data):
#     # print(mpu.acceleration)
#     emit('pong', mpu.acceleration) 

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True,port=5000, use_reloader=False)


