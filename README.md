# Audioset_preprocessing

[AudioSet](https://research.google.com/audioset/)의 메타데이터를 기반으로 YouTube에서 오디오만 다운로드하고, 세그먼트를 추출하며, `.wav` 형식으로 변환 및 전처리하는 파이프라인 스크립트입니다.

---

## 스크립트 구성

### 1. `extractor.py`

- AudioSet의 라벨에 해당하는 YouTube 오디오를 다운로드하고, 지정된 세그먼트를 잘라 `.wav`로 저장합니다.
- `class_labels_indices.csv`, `eval_segments.csv`, `unbalanced_train_segments.csv`를 사용합니다.

**How to use:**

```bash
python extractor.py --label Explosion --num_sample 10
```

### 2. `duration.py`

- 특정 폴더 내 .wav 파일들의 재생 시간을 측정하고 평균 길이를 계산합니다.

**How to use:**

```bash
python duration.py --folder audioset
```

### 3. `spec.py`

- 오디오 파일들의 spec을 .txt 파일로 저장합니다.
- 파일경로, 라벨, 샘플 길이(초), 라벨 평균 길이, 분산, 최소/최대 길이, 샘플레이트

**How to use:**

```bash
python spec.py --folder audioset --txt output_info.txt
```

### 4. `resampling.py`

- 오디오 파일의 FFT 주파수 분석을 통해 주요 주파수 대역을 확인하고, 최적의 샘플레이트로 리샘플링합니다.
- 결과 파일은 _resampled.wav 확장자로 저장됩니다.

**How to use:**

```bash
python resampling.py --folder audioset/Explosion
```

### Sturcture
audioset/
  ├── Fire_alarm/
  │   ├── Fire_alarm_0.wav
  │   ├── Fire_alarm_1.wav
  │   └── ...
  ├── Explosion/
  │   ├── Explosio_0.wav
  │   └── ...
class_labels_indices.csv
eval_segments.csv
unbalanced_train_segments.csv
extractor.py
duration.py
spec.py
resampling.py
