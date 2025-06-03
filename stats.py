import os
import argparse
import wave
import contextlib
import numpy as np
from collections import defaultdict

def get_duration(filepath):
    try:
        with contextlib.closing(wave.open(filepath, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration
    except wave.Error:
        return None

def scan_directory(directory):
    label_durations = defaultdict(list)

    for root, _, files in os.walk(directory):
        label = os.path.basename(root)
        for file in files:
            if file.endswith(".wav"):
                filepath = os.path.join(root, file)
                duration = get_duration(filepath)
                if duration is not None:
                    label_durations[label].append(duration)

    for label, durations in label_durations.items():
        durations_np = np.array(durations)
        avg = np.mean(durations_np)
        var = np.var(durations_np)
        min_d = np.min(durations_np)
        max_d = np.max(durations_np)
        print(f"Label: {label}")
        print(f"  Count      : {len(durations)}")
        print(f"  Avg length : {avg:.2f}")
        print(f"  Variance   : {var:.2f}")
        print(f"  Min length : {min_d:.2f}")
        print(f"  Max length : {max_d:.2f}\n")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    scan_directory(args.folder)

if __name__ == "__main__":
    main()
