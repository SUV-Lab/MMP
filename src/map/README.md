# Map Extraction Tools

이 디렉토리는 대용량 지형 데이터(merged.tif)에서 원하는 영역을 추출하는 도구들을 포함합니다.

## 🗺️ merged.tif 다운로드

대용량 지형 파일은 GitHub Release에서 다운로드하세요:

1. [Releases 페이지](https://github.com/limgyeonghun/MMP/releases)로 이동
2. 최신 릴리스에서 `merged.tif` 다운로드
3. 이 디렉토리(`src/map/`)에 배치

```bash
cd src/map/
# merged.tif를 이 디렉토리에 다운로드
```

## 🛠️ 사용법

### 1. 인터랙티브 추출 (권장)

GUI를 사용해서 마우스로 클릭하여 영역을 선택하고 추출합니다.

```bash
python3 interactive_extract.py
```

**기본 옵션:**
- `--input`: 입력 TIF 파일 (기본값: merged.tif)
- `--size`: 기본 추출 크기 (도 단위, 기본값: 0.8)
- `--output-dir`: 출력 디렉토리 (기본값: 현재 디렉토리)

**mmp_terrain/data로 직접 저장:**
```bash
python3 interactive_extract.py \
  --input merged.tif \
  --size 0.8 \
  --output-dir ../mmp_terrain/data/
```

**사용 방법:**
1. 전체 지도가 표시됩니다
2. 마우스를 움직이면 노란색 미리보기 사각형이 표시됩니다
3. 원하는 위치를 클릭하면 빨간색 선택 사각형이 표시됩니다
4. 크기 슬라이더로 추출 영역 크기를 조정합니다 (0.1° ~ 10°)
5. Output name에 파일명을 입력합니다
6. Extract 버튼을 눌러 저장합니다

**특징:**
- 마우스 호버로 실시간 미리보기
- 크기 조정 슬라이더 (약 11km ~ 1,110km)
- 자동 파일명 증분 (extracted.tif, extracted_2.tif, ...)

### 2. CLI 추출

중심점과 크기를 지정해서 추출합니다.

```bash
python3 extract_center.py \
  --input merged.tif \
  --output korea.tif \
  --lat 37.5 \
  --lon 127.5 \
  --size 0.8
```

**인자:**
- `--input`: 입력 TIF 파일
- `--output`: 출력 TIF 파일
- `--lat`: 중심 위도 (도)
- `--lon`: 중심 경도 (도)
- `--size`: 한 변의 크기 (도)

**예시:**

DMZ 지역 추출 (0.8° × 0.8°):
```bash
python3 extract_center.py \
  --input merged.tif \
  --output dmz_region.tif \
  --lat 38.4 \
  --lon 128.0 \
  --size 0.8
```

서해~산둥반도 지역 추출 (5° × 5°):
```bash
python3 extract_center.py \
  --input merged.tif \
  --output yellow_sea.tif \
  --lat 36.5 \
  --lon 124.0 \
  --size 5.0
```

## 📂 파일 구조

```
src/map/
├── README.md                  # 이 파일
├── interactive_extract.py     # 인터랙티브 GUI 추출 도구
├── extract_center.py          # CLI 중심점 기반 추출 도구
├── merged.tif                 # 전체 지형 데이터 (Git에서 제외, Release에서 다운로드)
└── *.tif                      # 추출된 지형 파일들 (Git에서 제외)
```

## 🎯 워크플로우

1. **merged.tif 준비**: GitHub Release에서 다운로드
2. **영역 추출**: `interactive_extract.py` 또는 `extract_center.py` 사용
3. **ROS2 패키지에서 사용**:
   - 추출된 TIF를 `src/mmp_terrain/data/`로 복사 또는
   - `--output-dir` 옵션으로 직접 저장

## 💡 팁

- **크기 선택**: 1° ≈ 111km, 0.8° ≈ 89km
- **파일 크기**: 작은 영역일수록 RViz에서 로딩이 빠릅니다
- **다중 추출**: 인터랙티브 도구에서 Extract 후 다시 클릭하면 여러 영역을 연속 추출할 수 있습니다

## 🐳 Docker 환경에서 실행 (추가 예정)

```bash

```
