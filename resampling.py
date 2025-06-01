import os
import argparse
import sys
import numpy as np
import soundfile as sf
from scipy.signal import resample
from scipy.fft import rfft, rfftfreq

def estimate_true_sr(y, sr):

    N = len(y)
    yf = np.abs(rfft(y))
    xf = rfftfreq(N, 1 / sr)

    power = yf / np.sum(yf)
    threshold = np.percentile(power, 98)  # 고주파 성분 포함을 위해 상위 2% 에너지 기준
    significant_freqs = xf[power >= threshold]

    if len(significant_freqs) == 0:
        return sr  # 측정 실패시 원래 SR

    f_max = np.max(significant_freqs)
    estimated_sr = int(np.ceil(f_max * 2))

    return estimated_sr


def resample_audio(input_path, output_path):
    y, sr = sf.read(input_path)

    true_sr = estimate_true_sr(y, sr)

    num_samples = int(len(y) * true_sr / sr)
    y_resampled = resample(y, num_samples)

    sf.write(output_path, y_resampled, true_sr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True)
    parser.add_argument("--num_sample", type=str, default="all",
                        help='number of samples to process or "all" (default)')
    args = parser.parse_args()

    if args.num_sample.lower() == "all":
        num_sample = None
    else:
        try:
            num_sample = int(args.num_sample)
        except ValueError:
            sys.exit(1)

    wav_files = sorted([f for f in os.listdir(args.folder) if f.endswith(".wav") and not f.endswith("_resampled.wav")])

    if num_sample is not None:
        wav_files = wav_files[:num_sample]

    for fname in wav_files:
        input_path = os.path.join(args.folder, fname)
        name, ext = os.path.splitext(fname)
        output_path = os.path.join(args.folder, f"{name}_resampled.wav")
        resample_audio(input_path, output_path)


if __name__ == "__main__":
    main()
