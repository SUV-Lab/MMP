# MMP (Multi-Modal Planning)

ROS2 기반 지형 시각화 및 경로 계획 시스템

## 📦 패키지 구조

```
MMP/
├── src/
│   ├── mmp_terrain/          # 지형 데이터 로딩 및 퍼블리싱
│   ├── mmp_visualization/    # RViz 설정 및 시각화
│   └── map/                  # 지형 맵 추출 도구
└── README.md
```

## 🚀 빠른 시작

### 1. 지형 데이터 다운로드

MMP는 SRTM 기반 고해상도 지형 데이터를 사용합니다. 먼저 [GitHub Releases](https://github.com/limgyeonghun/MMP/releases)에서 `merged.tif`를 다운로드하세요.
(https://github.com/limgyeonghun/MMP/releases/download/terrain-data/merged.tif)

```bash
cd src/map/
# merged.tif를 이 디렉토리에 다운로드
```

### 2. 원하는 지역 추출

인터랙티브 GUI 도구를 사용해서 원하는 영역을 추출합니다:

```bash
cd src/map/
python3 interactive_extract.py --output-dir ../mmp_terrain/data/
```

또는 CLI로 직접 추출:

```bash
python3 extract_center.py \
  --input merged.tif \
  --output ../mmp_terrain/data/extract_world.tif \
  --lat 37.5 \
  --lon 127.5 \
  --size 0.8
```

자세한 사용법은 [src/map/README.md](src/map/README.md)를 참조하세요.

### 3. ROS2 빌드 (Docker 환경)

```bash
추가 예정
```

### 4. 실행

```bash
ros2 launch mmp_visualization mmp.launch.py
```

## 🐳 Docker 환경 (추가 예정)

프로젝트는 Docker 컨테이너 내에서 실행됩니다:

## 📐 좌표 참고

한반도 주요 지역:

| 지역 | 위도 | 경도 | 추천 크기 |
|------|------|------|-----------|
| 서울 | 37.5°N | 127.0°E | 0.5° |
| DMZ (강원 북부) | 38.4°N | 128.0°E | 0.8° |
| 부산 | 35.1°N | 129.0°E | 0.5° |
| 제주도 | 33.5°N | 126.5°E | 0.8° |
| 서해 중부 | 36.5°N | 124.0°E | 5.0° |

크기 참고: 1° ≈ 111km
