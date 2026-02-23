# MMP (Multi-Modal Planning)

ROS2 기반 지형 시각화 및 경로 계획 시스템

## 📦 패키지 구조

```
MMP/
├── map/                      # 지형 맵 다운로드 및 추출 도구
├── src/
│   ├── mmp_terrain/          # 지형 데이터 로딩 및 퍼블리싱
│   └── mmp_visualization/    # RViz 설정 및 시각화
│   └── mmp_pathplan/         # 경로 계획 알고리즘 (추후 추가)
│   └── mmp_obstacle/         # 동적 장애물 로딩 및 퍼블리싱 (추후 추가)
└── README.md
```

## 🚀 빠른 시작

### 1. SRTM 원본 데이터 다운로드

먼저 한반도 전체 SRTM 데이터를 다운로드합니다:

```bash
python3 map/download_terrain_data.py merged
```

데이터는 자동으로 `map/merged.tif`에 저장됩니다.

### 2. 원하는 지역 추출

인터랙티브 GUI 도구를 사용해서 원하는 영역을 추출합니다:

```bash
cd map/
python3 interactive_extract.py
```

추출된 데이터는 `src/mmp_terrain/data/`에 저장됩니다.

자세한 사용법은 [map/README.md](map/README.md)를 참조하세요.

### 3. ROS2 빌드 (Docker 환경)

```bash
추가 예정
```

### 4. 실행

```bash
# 기본 월드 (dokdo)
ros2 launch mmp_visualization mmp.launch.py

# 다른 월드 지정
ros2 launch mmp_visualization mmp.launch.py world:=korea
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
