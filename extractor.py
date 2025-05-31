import os
import subprocess
import argparse
import pandas as pd
from tqdm import tqdm

def slugify_spaces(name):
    return name.replace(" ", "_")

# 라벨 매핑
df = pd.read_csv("class_labels_indices.csv")
label_map = dict(zip(df["mid"], df["display_name"].apply(slugify_spaces)))

# yt-dlp로 오디오 다운로드 
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

#ffmpeg로 wav 변환
def convert_to_wav(temp_audio_path: str, output_path: str) :
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_audio_path,
            "-acodec", "pcm_s16le",
            "-ar", "48000",
            "-ac", "1",
            output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #출력 로그 숨김
        os.remove(temp_audio_path)
        return True
    except subprocess.CalledProcessError:
        return False


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", type=str, required=True)
    parser.add_argument("--num_sample", type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    target_label = args.label
    num_sample = args.num_sample
    temp_audio_path = "temp_audio.m4a"
    csv_files = ["eval_segments.csv", "unbalanced_train_segments.csv"]
    os.makedirs("./downloads", exist_ok=True)

    parsed_rows = []
    for file in csv_files:
        if not os.path.exists(file):
            continue
        with open(file, "r", encoding="utf-8") as f:
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

                label_list = parts[3].strip().strip('"').split()
                matched = [label_map[l] for l in label_list if l in label_map]
                if target_label in matched:
                    parsed_rows.append({
                        "YTID": video_id,
                        "start_seconds": start,
                        "end_seconds": end,
                        "label": target_label
                    })

    if not parsed_rows:
        return

    final_df = pd.DataFrame(parsed_rows[:num_sample * 2])  # 실패 대비 여유 확보

    os.makedirs(f"audioset/{target_label}", exist_ok=True)

    success_count = 0
    for _, row in tqdm(final_df.iterrows(), total=len(final_df), desc=f"Downloading: "):
        if success_count >= num_sample:
            break

        ytid = row["YTID"]
        start = row["start_seconds"]
        end = row["end_seconds"]
        duration = end - start
        url = f"https://www.youtube.com/watch?v={ytid}"
        output_path = f"audioset/{target_label}/{target_label}_{success_count}.wav"
        temp_full_wav = "temp_full.wav"
        # 오디오 다운로드 및 WAV 저장
        if not download_audio(url, temp_audio_path):
            continue

        if not convert_to_wav(temp_audio_path, temp_full_wav):
            continue

        # 세그먼트 자르기
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