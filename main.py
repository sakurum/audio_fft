#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np

class TerminalAudioSpectrum(object):
    """
    ターミナル上に棒グラフを動的に表示するクラス

    n_bar: バーの数
    height: バーの高さ（行数）
    max: 表示音量の最大値（y_limit）
    active_max: 動的にmaxを変更する
    slow_down: バーがゆっくり落ちるようにする
    bar: バーの文字を指定する
    """
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
                    levels[i] = self.prev_levels[i]-2
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


class AudioSpectrum(object):
    """
    オーディオ入力をFFTして、CHUNK毎のx, yを返す

    n_part: 生データをいくつに分割するか
    """
    def __init__(self, n_part):
        # pyaudio
        self.RATE = 44100
        self.CHUNK = 1024
        self.CHANNEL = 1
        self._p = pyaudio.PyAudio()
        self._stream = p.open(
            format=pyaudio.paInt16,
            channels=self.CHANNEL,
            rate=self.RATE,
            input=True
        )

        self.XLIM = 10000
        self.N_PART = n_part
        self.SENT = int(self.XLIM*self.CHUNK/self.RATE)

    def _read_stream(self):
        return self._stream.read(self.CHUNK)

    def _fft(self, buffer):
        # np.frombuffer() でbuffをndarrayに
        # np.split( ,2) でfxが正の部分のみ切り取る（対称なので半分いらない）
        y = np.split(np.abs(np.fft.fft(np.frombuffer(buffer, dtype='int16'))), 2)[0]
        x = np.split(np.fft.fftfreq(self.CHUNK, d=1.0/self.RATE), 2)[0]
        return x, y

    def _split(self, x, y):
        # y[:self.SENT] で表示する幅（0~XLIM）にあたる部分のみ切り取る
        # n等分して部分ごとの最大値をとる（x軸は周波数の目盛りになる）
        y = [np.max(yi) for yi in np.array_split(y[:self.SENT], self.N_PART)]
        x = [xi[0] for xi in np.array_split(x[:self.SENT], self.N_PART)]
        return x, y

    def get(self):
        return self._split(*self._fft(self._read_stream()))

    def get_raw(self):
        return self._fft(self._read_stream())

    def __del__(self):
        self._stream.close()
        self._p.terminate()


if __name__ == '__main__':
    N = 32
    a_spectrum = AudioSpectrum(n_part=N)
    ter_as = TerminalAudioSpectrum(n_bar=N, height=32, max=10000, bar="██")

    while True:
        x, y = a_spectrum.get()
        ter_as.show(y)
