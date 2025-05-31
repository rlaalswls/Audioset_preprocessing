import os
import argparse
import wave
import contextlib

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
    durations = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".wav"):
                filepath = os.path.join(root, file)
                duration = get_duration(filepath)
                if duration is not None:
                    durations.append(duration)
                    print(f"{filepath}: {duration:.2f} sec")
                else:
                    print(f"{filepath}: Unable to read")

    if durations:
        avg = sum(durations) / len(durations)
        print(f"Average duration: {avg:.2f} sec")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    scan_directory(args.folder)

if __name__ == "__main__":
    main()