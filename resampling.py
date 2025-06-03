import os
import sys
import argparse
import torchaudio
import torch
import numpy as np
from scipy.fft import rfft, rfftfreq

# 사용할 표준 샘플레이트
STANDARD_SRS = [8000, 16000, 22050, 32000, 44100, 48000]

def estimate_max_freq(waveform, sr):
    y = waveform.numpy().squeeze()
    N = len(y)
    yf = np.abs(rfft(y))
    xf = rfftfreq(N, 1 / sr)
    f_max = xf[np.argmax(yf)]
    return f_max

def get_nearest_standard_sr(max_freq):
    required_sr = int(np.ceil(max_freq * 2))
    for sr in STANDARD_SRS:
        if sr >= required_sr:
            return sr
    return STANDARD_SRS[-1]

def resample_and_save(input_path, output_path):
    waveform, sr = torchaudio.load(input_path)
    max_freq = estimate_max_freq(waveform, sr)
    target_sr = get_nearest_standard_sr(max_freq)

    if target_sr == sr:
        torchaudio.save(output_path, waveform, sr)
    else:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        resampled_waveform = resampler(waveform)
        torchaudio.save(output_path, resampled_waveform, target_sr)

    print(f"{os.path.basename(input_path)}: f_max = {max_freq:.1f} Hz → {target_sr} Hz")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True)
    parser.add_argument("--num_sample", type=str, default="all")
    args = parser.parse_args()

    # 샘플 수 처리
    if args.num_sample.lower() == "all":
        num_sample = None
    else:
        try:
            num_sample = int(args.num_sample)
        except ValueError:
            sys.exit(1)

    # wav 파일 리스트
    wav_files = sorted([
        f for f in os.listdir(args.folder)
        if f.endswith(".wav") and not f.endswith("_resampled.wav")
    ])

    if num_sample is not None:
        wav_files = wav_files[:num_sample]

    for fname in wav_files:
        input_path = os.path.join(args.folder, fname)
        name, ext = os.path.splitext(fname)
        output_path = os.path.join(args.folder, f"{name}_resampled.wav")
        resample_and_save(input_path, output_path)

if __name__ == "__main__":
    main()
