import os
import sys
import argparse
import torchaudio
import numpy as np
import torch
from scipy.fft import rfftfreq

# 사용할 표준 샘플레이트
STANDARD_SRS = [8000, 12000, 16000, 22050, 32000, 44100, 48000]

def estimate_max_freq(waveform, sr, n_fft=2048, hop_length=None):
    if hop_length is None:
        hop_length = n_fft // 4

    # STFT 수행: shape = (channel, freq_bins, time_steps)
    stft = torch.stft(
        waveform, 
        n_fft=n_fft, 
        hop_length=hop_length, 
        return_complex=True
    )

    # 진폭 스펙트럼 계산
    magnitude = stft.abs().squeeze(0).numpy()  # shape = (freq_bins, time_steps)
    max_bin_indices = np.argmax(magnitude, axis=0)
    max_bin = max(max_bin_indices)
    freqs = rfftfreq(n_fft, 1 / sr)
    f_max = freqs[max_bin] if max_bin < len(freqs) else freqs[-1]
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

    resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
    resampled_waveform = resampler(waveform)
    torchaudio.save(output_path, resampled_waveform, target_sr)

def process_label_folder(label_folder, num_sample):
    label = os.path.basename(label_folder)
    output_folder = os.path.join(label_folder, "resample")
    os.makedirs(output_folder, exist_ok=True)

    wav_files = sorted([f for f in os.listdir(label_folder) if f.endswith(".wav")])

    if num_sample is not None:
        wav_files = wav_files[:num_sample]

    for idx, fname in enumerate(wav_files):
        input_path = os.path.join(label_folder, fname)
        output_filename = f"{label}_resample_{idx}.wav"
        output_path = os.path.join(output_folder, output_filename)
        resample_and_save(input_path, output_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True)
    parser.add_argument("--num_sample", type=str, default="all")
    args = parser.parse_args()

    root_folder = args.folder.rstrip("/")

    if args.num_sample.lower() == "all":
        num_sample = None
    else:
        try:
            num_sample = int(args.num_sample)
        except ValueError:
            sys.exit(1)

    # 루트 폴더 바로 아래 .wav가 있으면 한 폴더만 처리
    if any(f.endswith(".wav") for f in os.listdir(root_folder)):
        process_label_folder(root_folder, num_sample)
    else:
        # 하위 폴더 각각 처리
        for label_name in sorted(os.listdir(root_folder)):
            label_folder = os.path.join(root_folder, label_name)
            if os.path.isdir(label_folder):
                process_label_folder(label_folder, num_sample)

if __name__ == "__main__":
    main()
