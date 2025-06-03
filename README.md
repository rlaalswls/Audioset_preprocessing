# Audioset_preprocessing

[AudioSet](https://research.google.com/audioset/)의 데이터를 기반으로,
`yt-dlp`를 사용하여 YouTube에서 오디오를 다운로드하고, 세그먼트를 추출한 뒤, `ffmpeg`로 .wav 형식 변환 및 전처리합니다.

## Required Dependencies

**Python venv (Recommended)**
```
python -m venv myvenv
#macOS/Linux:
source myvenv/bin/activate
```

**Install yt-dlp**
```
pip install -U yt-dlp
```

**Install ffmpeg**
```
Windows: https://ffmpeg.org/download.html#build-windows
macOS: brew install ffmpeg
Linux: sudo apt-get install ffmpeg
```

**Install Python libraries**
```
pip install pandas tqdm numpy soundfile scipy torchaudio
```

## Instruction

### 1. extractor.py

- AudioSet의 라벨에 해당하는 YouTube 오디오를 다운로드하고, 지정된 세그먼트를 잘라 `.wav`로 저장합니다.
- --label 인자에는 AudioSet의 'display_name' 값을 사용합니다. 큰 따옴표(" ")로 감싸야 합니다.

**How to use:**

```bash
python extractor.py --label "Fire alarm" --num_sample 10
```

### 2. stats.py

- 라벨 별 평균 길이, 분산, 최소/최대 길이를 계산합니다.

**How to use:**

```bash
python stats.py --folder audioset
```

### 3. spec.py

- 오디오 파일들의 spec을 .txt 파일로 저장합니다.
- 파일경로, 라벨, 샘플 길이(초), 샘플레이트

**How to use:**

```bash
python spec.py --folder audioset --txt output_info.txt
```

### 4. resampling.py

- 오디오 파일의 FFT 주파수 분석을 통해 주파수 대역을 확인하고, 최적의 샘플레이트로 리샘플링합니다.
- 결과 파일은 _resampled.wav로 저장됩니다.

**How to use:**

```bash
python resampling.py --folder audioset/Explosion --num_sample all
```

### Sturcture
```
├── audioset/              
│   └── Fire_alarm/
│       ├── Fire_alarm_0.wav
│       ├── Fire_alarm_1.wav
│       └── ...
│   └── Explosion/
│       ├── Explosion_0.wav
│       └── ...
├── class_labels_indices.csv
├── eval_segments.csv
├── unbalanced_train_segments.csv
├── extractor.py
├── duration.py
├── spec.py
├── resampling.py
├── requirements.txt
└── README.md                       
```
