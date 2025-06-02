import os
import subprocess
import argparse
import pandas as pd
from tqdm import tqdm

def slugify(name):
    # class_labels_indices.csv의 display_name은 공백 있음.
    # 사용자 입력에서 "_"와 " " 구분 없이 받으려면 이렇게 처리 가능
    return name.strip().lower().replace("_", " ")

def download_audio(youtube_url: str, temp_audio_path: str):
    try:
        subprocess.run([
            "yt-dlp",
            "-f", "bestaudio[ext=m4a]/bestaudio",
            "-o", temp_audio_path,
            youtube_url
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def convert_to_wav(temp_audio_path: str, output_path: str):
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_audio_path,
            "-acodec", "pcm_s16le",
            "-ar", "48000",
            "-ac", "1",
            output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(temp_audio_path)
        return True
    except subprocess.CalledProcessError:
        return False

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", type=str, required=True)
    parser.add_argument("--num_sample", type=str, required=True)
    args = parser.parse_args()

    if args.num_sample.lower() == "all":
        args.num_sample = None
    else:
        try:
            args.num_sample = int(args.num_sample)
        except ValueError:
            parser.error("--num_sample must be an integer or 'all'")

    return args

def main():
    args = parse_args()
    input_label_name = slugify(args.label)  # 입력받은 라벨명 공백과 _ 처리
    num_sample = args.num_sample
    temp_audio_path = "temp_audio.m4a"
    data_file = "./audioset/data.txt"
    label_csv = "./class_labels_indices.csv"

    # class_labels_indices.csv 읽기
    if not os.path.exists(label_csv):
        print(f"Label CSV file not found: {label_csv}")
        return

    df_labels = pd.read_csv(label_csv)
    # display_name도 slugify 해서 매핑 준비 (key: slugify(display_name), value: mid)
    labelname_to_mid = {slugify(name): mid for mid, name in zip(df_labels["mid"], df_labels["display_name"])}

    if input_label_name not in labelname_to_mid:
        print(f"Label '{args.label}' not found in label list.")
        print("Available labels include:")
        for k in list(labelname_to_mid.keys())[:20]:
            print(f"  - {k}")
        return

    target_label_id = labelname_to_mid[input_label_name]

    parsed_rows = []
    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", 3)
            if len(parts) != 4:
                continue

            video_id = parts[0].strip()
            try:
                start = float(parts[1].strip())
                end = float(parts[2].strip())
            except ValueError:
                continue

            label_ids_str = parts[3].strip().strip('"')
            label_ids = [l.strip() for l in label_ids_str.split(",")]

            if target_label_id in label_ids:
                parsed_rows.append({
                    "YTID": video_id,
                    "start_seconds": start,
                    "end_seconds": end,
                    "label_id": target_label_id
                })

    if not parsed_rows:
        print(f"No segments found for label '{args.label}' ({target_label_id}).")
        return

    # 여유분 확보 (2배)
    final_rows = parsed_rows if num_sample is None else parsed_rows[:num_sample * 2]

    safe_label_folder = target_label_id.lstrip("/").replace("/", "_")
    os.makedirs(f"audioset/{safe_label_folder}", exist_ok=True)

    success_count = 0
    for row in tqdm(final_rows, desc=f"Downloading '{args.label}' samples", ncols=100):
        if num_sample is not None and success_count >= num_sample:
            break

        ytid = row["YTID"]
        start = row["start_seconds"]
        end = row["end_seconds"]
        duration = end - start
        url = f"https://www.youtube.com/watch?v={ytid}"
        output_path = f"audioset/{safe_label_folder}/{safe_label_folder}_{success_count}.wav"
        temp_full_wav = "temp_full.wav"

        if not download_audio(url, temp_audio_path):
            continue

        if not convert_to_wav(temp_audio_path, temp_full_wav):
            continue

        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_full_wav,
                "-ss", str(start),
                "-t", str(duration),
                output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            success_count += 1
        except subprocess.CalledProcessError:
            continue

    if os.path.exists(temp_full_wav):
        os.remove(temp_full_wav)

if __name__ == "__main__":
    main()
