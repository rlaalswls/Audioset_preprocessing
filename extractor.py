import os
import subprocess
import argparse
import json
from tqdm import tqdm

def slugify(name):
    return name.strip().replace("_", " ")

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
    input_label_name = slugify(args.label)
    num_sample = args.num_sample
    temp_audio_path = "temp_audio.m4a"
    label_json = "./audioset2/ontology.json" 
    segment_files = ["unbalanced_train_segments.csv", "eval_segments.csv"]

    # JSON 파일 읽기 및 label name → id 매핑
    with open(label_json, "r", encoding="utf-8") as f:
        ontology = json.load(f)
    labelname_to_mid = {slugify(item["name"]): item["id"] for item in ontology}

    target_label_id = labelname_to_mid[input_label_name]

    parsed_rows = []
    for data_file in segment_files:
        if not os.path.exists(data_file):
            continue

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

    final_rows = parsed_rows

    os.makedirs("audioset", exist_ok=True)
    label_prefix = args.label.replace(" ", "_")
    os.makedirs(f"audioset/{label_prefix}", exist_ok=True)

    success_count = 0
    fail_count = 0
    temp_full_wav = "temp_full.wav"

    for row in tqdm(final_rows, desc=f"Downloading '{args.label}' samples", ncols=100, leave=False, dynamic_ncols=True):
        if num_sample is not None and success_count >= num_sample:
            break

        ytid = row["YTID"]
        start = row["start_seconds"]
        end = row["end_seconds"]
        duration = end - start
        url = f"https://www.youtube.com/watch?v={ytid}"
        output_path = f"audioset/{label_prefix}/{label_prefix}_{success_count}.wav"

        if not download_audio(url, temp_audio_path):
            fail_count += 1
            continue

        if not convert_to_wav(temp_audio_path, temp_full_wav):
            fail_count += 1
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
            fail_count += 1
            continue

    if os.path.exists(temp_full_wav):
        os.remove(temp_full_wav)

    print(f"누락 : {fail_count}개")

if __name__ == "__main__":
    main()
