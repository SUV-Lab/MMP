#!/usr/bin/env python3
"""
Terrain Data Downloader for MMP Project
Downloads terrain elevation data (GeoTIFF files) for mission planning.
"""

import os
import sys
import urllib.request
import hashlib
from pathlib import Path


# Terrain data registry
TERRAIN_DATA = {
    'merged': {
        'filename': 'merged.tif',
        'description': 'Korean Peninsula - Full SRTM data for extraction',
        'url': 'https://github.com/limgyeonghun/MMP/releases/download/terrain-data/merged.tif',
        'sha256': '9d61f73cedb1ebaa73f139cc552a4ec78095d39803e74ad408bb4cbbc790d9c1',  # TODO: Add checksum after uploading
        'size_mb': 618,  # Approximate size
        'save_to_map': True,  # Save to map/ directory instead of data/
    }
}

def get_data_directory(save_to_map=False):
    script_dir = Path(__file__).parent

    if save_to_map:
        data_dir = script_dir
    else:
        data_dir = script_dir / 'src' / 'mmp_terrain' / 'data'

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_file(filepath, expected_hash):
    if expected_hash is None:
        print(f"  ⚠️  Warning: No checksum available for verification")
        return True

    print(f"  Verifying file integrity...")
    actual_hash = calculate_sha256(filepath)

    if actual_hash == expected_hash:
        print(f"  ✓ File integrity verified")
        return True
    else:
        print(f"  ✗ Checksum mismatch!")
        print(f"    Expected: {expected_hash}")
        print(f"    Got:      {actual_hash}")
        return False


def download_file(url, dest_path, expected_size_mb=None):
    print(f"  Downloading from: {url}")
    print(f"  Destination: {dest_path}")

    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print()
        return True
    except Exception as e:
        print(f"\n  ✗ Download failed: {e}")
        return False


def download_terrain(region_key):
    if region_key not in TERRAIN_DATA:
        print(f"Error: Unknown region '{region_key}'")
        print(f"Available regions: {', '.join(TERRAIN_DATA.keys())}")
        return False

    data_info = TERRAIN_DATA[region_key]
    save_to_map = data_info.get('save_to_map', False)
    data_dir = get_data_directory(save_to_map)
    dest_path = data_dir / data_info['filename']

    print(f"\n{'='*60}")
    print(f"Downloading: {region_key}")
    print(f"Description: {data_info['description']}")
    print(f"Size: ~{data_info['size_mb']} MB")
    print(f"{'='*60}\n")

    if dest_path.exists():
        print(f"  File already exists: {dest_path}")

        if data_info['sha256']:
            if verify_file(dest_path, data_info['sha256']):
                print(f"  ✓ File is valid, skipping download")
                return True
            else:
                print(f"  File is corrupted, re-downloading...")
                dest_path.unlink()
        else:
            response = input("  File exists but cannot verify. Re-download? (y/N): ")
            if response.lower() != 'y':
                print(f"  Using existing file")
                return True
            dest_path.unlink()

    if not download_file(data_info['url'], dest_path, data_info['size_mb']):
        return False

    if not verify_file(dest_path, data_info['sha256']):
        print(f"  Removing corrupted file...")
        dest_path.unlink()
        return False

    print(f"\n✓ Successfully downloaded: {dest_path}")
    return True


def list_available_data():
    print("\nAvailable terrain datasets:")
    print("=" * 60)

    for key, info in TERRAIN_DATA.items():
        print(f"\n  {key}")
        print(f"    Description: {info['description']}")
        print(f"    Size: ~{info['size_mb']} MB")
        print(f"    File: {info['filename']}")

    print("\n" + "=" * 60)


def check_installed_data():
    print("\nInstalled terrain data:")
    print("=" * 60)

    found_any = False
    for key, info in TERRAIN_DATA.items():
        save_to_map = info.get('save_to_map', False)
        data_dir = get_data_directory(save_to_map)
        filepath = data_dir / info['filename']

        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"\n  ✓ {key}")
            print(f"    Path: {filepath}")
            print(f"    Size: {size_mb:.1f} MB")
            found_any = True

    if not found_any:
        print("\n  No terrain data installed yet.")
        print("  Run with 'all' or specific region name to download.")

    print("\n" + "=" * 60)


def main():
    # 인자 없으면 merged 다운로드 (기본 동작)
    if len(sys.argv) < 2:
        return 0 if download_terrain('merged') else 1

    command = sys.argv[1]

    if command == 'list':
        list_available_data()
        return 0

    elif command == 'check':
        check_installed_data()
        return 0

    else:
        # 특정 데이터셋 다운로드
        if download_terrain(command):
            return 0
        else:
            return 1

if __name__ == '__main__':
    sys.exit(main())
