# Map Tools

지형 데이터 다운로드 및 추출 도구

## 📋 순서

### 1. 원본 데이터 다운로드

```bash
python3 download_terrain_data.py
```

→ `merged.tif` 다운로드 (618MB)

### 2. 원하는 지역 추출

```bash
python3 interactive_extract.py
```

→ 자동으로 `../src/mmp_terrain/data/xxx.tif`에 저장됨

## 🛠️ 도구 설명

### interactive_extract.py (권장)

GUI를 사용해서 마우스로 영역을 선택하고 추출합니다.

```bash
# 기본 실행 (자동으로 ../src/mmp_terrain/data/에 저장)
python3 interactive_extract.py

# 다른 디렉토리에 저장하려면
python3 interactive_extract.py --output-dir ./custom_dir/
```

**사용 방법:**
1. 전체 지도가 표시됨
2. 마우스를 움직이면 노란색 미리보기 표시
3. 클릭하면 빨간색 선택 영역 표시
4. 슬라이더로 크기 조정 (0.1° ~ 10°)
5. 파일명 입력 후 Extract 버튼 클릭

### extract_center.py

중심 좌표와 크기를 지정해서 추출합니다.

```bash
python3 extract_center.py \
  --input merged.tif \
  --output ../src/mmp_terrain/data/seoul.tif \
  --lat 37.5 \
  --lon 127.0 \
  --size 0.5
```

**주요 인자:**
- `--lat`: 중심 위도
- `--lon`: 중심 경도
- `--size`: 한 변의 크기 (도 단위, 1° ≈ 111km)

## 📐 좌표 참고

| 지역 | 위도 | 경도 | 추천 크기 |
|------|------|------|-----------|
| 서울 | 37.5°N | 127.0°E | 0.5° |
| DMZ (강원 북부) | 38.4°N | 128.0°E | 0.8° |
| 부산 | 35.1°N | 129.0°E | 0.5° |
| 제주도 | 33.5°N | 126.5°E | 0.8° |
| 서해 중부 | 36.5°N | 124.0°E | 5.0° |

크기 참고: 1° ≈ 111km

## 📂 디렉토리 구조

```
map/
├── download_terrain_data.py     # 원본 데이터 다운로드
├── interactive_extract.py        # GUI 추출 도구
├── extract_center.py             # CLI 추출 도구
├── merged.tif                    # 다운로드된 원본 (git ignore)
└── README.md                     # 이 파일
```

추출된 파일은 `../src/mmp_terrain/data/`에 저장됩니다.
