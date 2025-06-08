import csv
import os
import subprocess
from shutil import copyfile

# defaults
DEFAULT_LABEL_FILE = '../data/class_labels_indices.csv'
DEFAULT_CSV_DATASET = '../data/unbalanced_train_segments.csv'
DEFAULT_DEST_DIR = '../output/'
DEFAULT_FS = 16000


def find(class_name, args):
    print("Finding examples for class " + class_name + " in: " + args.audio_data_dir)
    dst_dir = args.destination_dir if args.destination_dir else DEFAULT_DEST_DIR
    dst_dir_path = os.path.join(dst_dir, class_name)
    csv_dataset = args.csv_dataset if args.csv_dataset else DEFAULT_CSV_DATASET
    class_id = get_label_id(class_name, args)
    youtube_ids = get_yt_ids(class_id, csv_dataset)
    find_files(youtube_ids, args.audio_data_dir, dst_dir_path)


def download(class_name, args):
    new_csv = create_csv(class_name, args)
    dst_dir_root = args.destination_dir if args.destination_dir else DEFAULT_DEST_DIR
    dst_dir = os.path.join(dst_dir_root, class_name)

    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    with open(new_csv) as dataset:
        reader = csv.reader(dataset)
        for row in reader:
            video_id, start_time = row[0], row[1]
            out_path = os.path.join(dst_dir, f"{video_id}_{start_time}.wav")
            download_audio_clip(video_id, start_time, out_path)


def download_audio_clip(video_id, start_time, out_path, duration=10):
    try:
        result = subprocess.run(
            ['yt-dlp', '-f', 'bestaudio', '-g', f'https://www.youtube.com/watch?v={video_id}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        ffmpeg_cmd = [
            'ffmpeg', '-ss', str(start_time), '-t', str(duration),
            '-i', url, '-ar', str(DEFAULT_FS), '-ac', '1', '-y', out_path
        ]
        subprocess.run(ffmpeg_cmd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] yt-dlp or ffmpeg failed for video {video_id}:\n{e.stderr}")


def create_csv(class_name, args):
    dst_dir = args.destination_dir if args.destination_dir else DEFAULT_DEST_DIR
    csv_dataset = args.csv_dataset if args.csv_dataset else DEFAULT_CSV_DATASET
    new_csv_path = os.path.join(dst_dir, f"{class_name}.csv")

    if os.path.isfile(new_csv_path):
        print(f"*** Overwriting {new_csv_path} ***")

    label_id = get_label_id(class_name, args)

    blacklisted_ids = []
    if args.blacklist:
        blacklisted_ids = [id for b in args.blacklist for id in get_label_id(b, args)]

    with open(csv_dataset) as dataset, open(new_csv_path, 'w', newline='') as new_csv:
        reader = csv.reader(dataset, skipinitialspace=True)
        writer = csv.writer(new_csv)
        to_write = [row for row in reader for label in label_id if label in row[3] and not set(row[3].split(",")).intersection(blacklisted_ids)]
        writer.writerows(to_write)

    print("Finished writing CSV file for " + class_name)
    return new_csv_path


def get_label_id(class_name, args):
    label_file_path = args.label_file if args.label_file else DEFAULT_LABEL_FILE
    with open(label_file_path) as label_file:
        reader = csv.DictReader(label_file)
        id_field = reader.fieldnames[1]
        name_field = reader.fieldnames[2]
        if args.strict:
            label_ids = [row[id_field] for row in reader if class_name.lower() == row[name_field].lower()]
        else:
            label_ids = [row[id_field] for row in reader if class_name.lower() in row[name_field].lower()]

        if not label_ids:
            print("No id for class " + class_name)
        elif len(label_ids) > 1:
            print("Multiple labels found for " + class_name)
            print(label_ids)
        else:
            print("Label ID for \"" + class_name + "\": " + str(label_ids))
    return label_ids


def get_yt_ids(label_ids, csv_path):
    yt_ids = {label: [] for label in label_ids}
    with open(csv_path) as dataset:
        reader = csv.reader(dataset, skipinitialspace=True)
        for row in reader:
            for label in label_ids:
                if label in row[3]:
                    yt_ids[label].append(row[0])

    for label in list(yt_ids):
        if not yt_ids[label]:
            print("No clips found for " + label)
            yt_ids.pop(label)
        else:
            print(f"Youtube ids for label {label} ({len(yt_ids[label])} found)")
    return yt_ids


def find_files(yt_ids, file_dir, dst_dir=None):
    dst_dir = file_dir if dst_dir is None else dst_dir
    for class_name in yt_ids:
        class_dir = os.path.join(dst_dir, class_name)
        os.makedirs(class_dir, exist_ok=True)
    for file in os.listdir(file_dir):
        for class_name, yt_id_list in yt_ids.items():
            if any(yt_id in file for yt_id in yt_id_list):
                src = os.path.join(file_dir, file)
                dst = os.path.join(dst_dir, class_name, file)
                copyfile(src, dst)
    print("Finished sorting files")
