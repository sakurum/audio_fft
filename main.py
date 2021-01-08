#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np
import threading
import queue as libqueue
import time

CHANNEL = 1
RATE = 44100
CHUNK = 1024
XLIM = 10000

class AudioStream():
    def __init__(self, queue):
        self.RATE = RATE
        self.CHUNK = CHUNK
        self.CHANNEL = CHANNEL
        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(
            format=pyaudio.paInt16,
            channels=self.CHANNEL,
            rate=self.RATE,
            input=True
        )
        self._queue = queue

    def start_read_stream(self):
        self._stream.start_stream()
        while self._stream.is_active():
            self._queue.put(self._stream.read(self.CHUNK))

    def __del__(self):
        self._stream.close()
        self._p.terminate()


class AudioSpectrum():
    def __init__(self, queue, n_part):
        self.XLIM = XLIM
        self.CHUNK = CHUNK
        self.RATE = RATE
        self.N_PART = n_part
        self.SENT = int(self.XLIM*self.CHUNK/self.RATE)
        self._queue = queue

    def _get_buffer_array(self):
        while True:
            if not self._queue.empty():
                return self._queue.get_nowait()
            else:
                time.sleep(0.001)


    def get_spectrum(self):
        # FFT, split
        y = np.split(np.abs(np.fft.fft(
                np.frombuffer(self._get_buffer_array(),
                dtype='int16'
            ))), 2)[0]
        x = np.split(np.fft.fftfreq(self.CHUNK, d=1.0/self.RATE), 2)[0]

        # split (n等分)
        y = [np.max(yi) for yi in np.array_split(y[:self.SENT], self.N_PART)]
        x = [xi[0] for xi in np.array_split(x[:self.SENT], self.N_PART)]

        return x, y


class TerminalAudioSpectrum():
    def __init__(self, n_bar, height, max=100000, active_max=True, slow_down=True, bar="██"):
        self.n_bar = n_bar
        self.height = height
        self.prev_levels = [0]*n_bar
        self.max = max
        self.active_max = active_max
        self.max_values = [self.max]*20
        self.bar = bar
        self.blank = " "*len(bar)
        self.slow_down = slow_down

        print("Use Ctrl-C to terminate")

    def show(self, y):
        # 動的に最大値を変える
        if self.active_max:
            self.max_values.pop()
            self.max_values.append(np.max(y))
            self.max = np.max(self.max_values)*1.2

        # 各々のバーの高さを計算
        levels = [yi//(self.max/self.height) for yi in y]

        # ゆっくりバーが落ちる処理
        if self.slow_down:
            for i in range(len(levels)):
                if levels[i] < self.prev_levels[i]:
                    levels[i] = self.prev_levels[i]*0.9
                self.prev_levels[i] = levels[i]

        # 出力する文字列を作成
        bar_str = ""
        for i in reversed(range(self.height)):
            for level in levels:
                bar_str += " "
                bar_str += self.bar if level>=i else self.blank
            bar_str += "\n"
        bar_str += "\033[{}A".format(self.height)

        print(bar_str, end="")

    def __del__(self):
        bar_str = ((" "+self.blank)*self.n_bar + "\n")*self.height
        bar_str += "\033[{}A".format(self.height)
        print(bar_str)


def pyaudio_deamon(queue):
    audio_stream = AudioStream(queue)
    audio_stream.start_read_stream()


def spectrum_deamon(queue):
    # N = 16
    N = 50

    l_cut = 3
    h_cut = 8
    spectrum = AudioSpectrum(queue, N)

    # a_terminal = TerminalAudioSpectrum(N-l_cut-h_cut, 10, bar="██████")
    a_terminal = TerminalAudioSpectrum(N-l_cut-h_cut, 20, bar="███")


    while True:
        x, y = spectrum.get_spectrum()
        a_terminal.show(y[l_cut:-h_cut])

def main():
    queue = libqueue.Queue()

    t_pyaudio = threading.Thread(name="pyaudio_deamon", target=pyaudio_deamon, args=(queue,))
    t_specturm = threading.Thread(name="spectrum_deamon", target=spectrum_deamon, args=(queue,))

    t_pyaudio.start()
    t_specturm.start()


if __name__ == '__main__':
    main()
