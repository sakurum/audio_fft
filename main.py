#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np
import matplotlib.pyplot as plt

# IDEA:
# 低い音 -> 青系

RATE = 44100
CHUNK = 1024
CHANNEL = 1

XLIM = 10000


def main():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNEL,
        rate=RATE,
        input=True
    )
    stream.stop_stream()

    max_buf = [100000]*10

    while True:
        stream.start_stream()
        buff = stream.read(CHUNK)
        stream.stop_stream()

        fy = np.abs(np.fft.fft(np.frombuffer(buff, dtype='int16')))
        fx = np.fft.fftfreq(CHUNK, d=1.0/RATE)

        fy = np.split(fy, 2)[0]
        fx = np.split(fx, 2)[0]

        a = int(XLIM*CHUNK/RATE)

        fy = fy[:a]
        fx = fx[:a]

        n_part = 32

        y_s = np.array_split(fy, n_part)
        y = [np.max(yi) for yi in y_s]

        x_s = np.array_split(fx, n_part)
        x = [xi[0] for xi in x_s]

        max_buf.pop()
        max_buf.append(np.max(y))

        """
        plt.plot(x, y)

        plt.ylim(0, np.mean(max_buf))
        plt.xlim(0, 10000)

        plt.pause(0.1)
        plt.cla()
        """

        ter_print(n_part, y, np.mean(max_buf), 32)


def ter_print(n, y, max, h):

    s = max/h
    levels = [yi//s for yi in y]

    for i in reversed(range(h)):
        for level in levels:
            if level >= i:
                print(" ███", end="")
            else:
                print("    ", end="")
        print("")
    print("\033[{}A".format(h), end="")


if __name__ == '__main__':
    main()