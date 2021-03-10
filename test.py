# import time
# import board
# import busio
# import adafruit_mpu6050
 
# i2c = busio.I2C(board.SCL, board.SDA)
# mpu = adafruit_mpu6050.MPU6050(i2c)

# while True:
#     print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (mpu.acceleration))
#     # print("Gyro X:%.2f, Y: %.2f, Z: %.2f degrees/s" % (mpu.gyro))
#     # print("Temperature: %.2f C" % mpu.temperature)
#     # print("")
#     time.sleep(0.1)

# import pyaudio
# p = pyaudio.PyAudio()
# for ii in range(p.get_device_count()):
#     print(p.get_device_info_by_index(ii).get('name'))


import pyaudio
import wave

import signal
import sys
import time
from queue import Queue

FORMAT = pyaudio.paInt16
CHANNELS = 1
samp_rate = 44100 # 44.1kHz sampling rate
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 0.5 # seconds to record
dev_index = 2 # device index found by p.get_device_info_by_index(ii)
# wav_output_filename = 'test1.wav' # name of .wav file

audio1 = pyaudio.PyAudio() # create pyaudio instantiation

sampleRate = 44100
bitsPerSample = 16
channels = 1

for ii in range(audio1.get_device_count()):
	print(audio1.get_device_info_by_index(ii).get('name'))

q = Queue()

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
wav_header = genHeader(sampleRate, bitsPerSample, channels)

def callback(in_data, frame_count, time_info, flag):
	global first_packet
	if first_packet:
		q.put(wav_header+in_data)
		first_packet= False;
	else:
		q.put(in_data)
	# print(in_data)
	return (in_data, pyaudio.paContinue)

# create pyaudio stream
stream = audio1.open(format=FORMAT, channels=CHANNELS,
				rate=RATE, input=True,input_device_index=2,
				frames_per_buffer=CHUNK, stream_callback=callback)
print("recording")



def signal_handler(sig, frame):
	print('You pressed Ctrl+C!')
	stream.stop_stream()
	stream.close()
	audio1.terminate()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
# signal.pause()

# q.put(1)

while True:
	print(q.get(True))
	# time.sleep(1)



# loop through stream and append audio chunks to frame array
# for ii in range(0,int((samp_rate/chunk)*record_secs)):
#     data = stream.read(chunk)
#     frames.append(data)

# print("finished recording")

# stop the stream, close it, and terminate the pyaudio instantiation


# save the audio frames as .wav file
# wavefile = wave.open(wav_output_filename,'wb')
# wavefile.setnchannels(chans)
# wavefile.setsampwidth(audio.get_sample_size(form_1))
# wavefile.setframerate(samp_rate)
# wavefile.writeframes(b''.join(frames))
# wavefile.close()