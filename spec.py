import os
import re
import argparse
import wave
import contextlib

def get_duration_samplerate(path):
    try:
        with contextlib.closing(wave.open(path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration, rate
    except:
        return None, None

def wav_info(folder):
    wav_data = {}

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".wav"):
                full_path = os.path.join(root, file)
                label = os.path.basename(os.path.dirname(full_path))  # 바로 상위 폴더를 라벨로 간주
                duration, samplerate = get_duration_samplerate(full_path)
                if duration is None:
                    continue

                if label not in wav_data:
                    wav_data[label] = []

                wav_data[label].append({
                    "path": full_path,
                    "duration": duration,
                    "samplerate": samplerate
                })

    return wav_data

def natural_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def write_txt(wav_data, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for label, entries in wav_data.items():
            entries = sorted(entries, key=lambda x: natural_key(x["path"]))
            for entry in entries:
                line = f"{entry['path']}\t{label}\t{entry['duration']:.2f}\t{entry['samplerate']}\n"
                f.write(line)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True)
    parser.add_argument("--txt", type=str, required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    wav_data = wav_info(args.folder)
    write_txt(wav_data, args.txt)

if __name__ == "__main__":
    main()
