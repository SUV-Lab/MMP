# MMP Terrain

A ROS2 package that publishes terrain elevation data as GridMap messages.

## Installation

### 1. Install Dependencies

```bash
pip3 install rasterio numpy
```

### 2. Download Terrain Data

```bash
cd src/mmp_terrain
python3 scripts/download_terrain_data.py korea
```

Check available datasets:
```bash
python3 scripts/download_terrain_data.py list
```

Check installed data:
```bash
python3 scripts/download_terrain_data.py check
```

Download all datasets:
```bash
python3 scripts/download_terrain_data.py all
```

### 3. Git LFS (Optional)

This project uses Git LFS to manage large terrain files. Install Git LFS to download automatically upon git clone:

```bash
# Ubuntu/Debian
sudo apt-get install git-lfs
git lfs install

# Pull Git LFS files
git lfs pull
```

*Note: You can still fetch data using the download script above without Git LFS.*

## Usage

### Run via Launch File

```bash
# Default world (dokdo)
ros2 launch mmp_visualization mmp.launch.py

# Specify different world
ros2 launch mmp_visualization mmp.launch.py world:=korea
ros2 launch mmp_visualization mmp.launch.py world:=seoul
```

### Run Node Directly

```bash
# Default world (dokdo)
ros2 run mmp_terrain terrain_publisher

# Specify different world
ros2 run mmp_terrain terrain_publisher --ros-args -p world:=korea
```

## Published Topics

- `/terrain/grid_map` (`grid_map_msgs/msg/GridMap`)
  - **Layer:** `elevation` (normalized elevation values)
  - **QoS:** RELIABLE, TRANSIENT_LOCAL
  - **Frame:** `map`

## Configuration

You can adjust the following parameters at the top of `terrain_publisher.py`:

```python
TARGET_CELL_SIZE_M = 500.0  # GridMap cell size (meters)
TARGET_SCALE = 10           # Downsampling ratio
```

## Troubleshooting

### "Terrain data file not found" error

Data has not been downloaded. Run:
```bash
python3 scripts/download_terrain_data.py korea
```

### Build error: "can't copy data/xxx.tif: doesn't exist"

This happens when you delete/add `.tif` files in the `data/` directory. The build system caches the old file list.

**Solution:** Clean the build cache and rebuild:
```bash
rm -rf build/mmp_terrain install/mmp_terrain
colcon build --packages-select mmp_terrain
```

Or clean the entire workspace:
```bash
rm -rf build install
colcon build
```

### Download script fails

The actual download URL might not be set in the `TERRAIN_DATA` dictionary inside `scripts/download_terrain_data.py`.

To manually use an existing file:
```bash
# Create data directory if it doesn't exist
mkdir -p src/mmp_terrain/data
# Copy or move the existing file
cp /path/to/your/korea.tif src/mmp_terrain/data/
```