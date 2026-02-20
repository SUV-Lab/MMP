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
# 나중에 여러 지역/해상도 추가 가능
TERRAIN_DATA = {
    'korea': {
        'filename': 'korea.tif',
        'description': 'Korean Peninsula - Full coverage (low resolution)',
        'url': 'https://github.com/limgyeonghun/MMP/releases/download/terrain-data-v1.0/korea.tif',
        # 실제 파일의 SHA256 해시값 (무결성 검증용)
        'sha256': 'ad72a1c0c92c2adca3da39a21888fdfeb14bc5f271fb55a569a85df18a2fb5dc',
        'size_mb': 176,
    },
    # 향후 추가 가능한 데이터셋 예시:
    # 'korea_central_hires': {
    #     'filename': 'korea_central_10m.tif',
    #     'description': 'Central Korea - High resolution (10m)',
    #     'url': '...',
    #     'sha256': '...',
    #     'size_mb': 500,
    # },
}


def get_data_directory():
    """데이터 저장 디렉토리 경로 반환"""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def calculate_sha256(filepath):
    """파일의 SHA256 해시값 계산"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_file(filepath, expected_hash):
    """파일 무결성 검증"""
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
    """파일 다운로드 (진행률 표시)"""
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
        print()  # 줄바꿈
        return True
    except Exception as e:
        print(f"\n  ✗ Download failed: {e}")
        return False


def download_terrain(region_key):
    """특정 지역의 terrain 데이터 다운로드"""
    if region_key not in TERRAIN_DATA:
        print(f"Error: Unknown region '{region_key}'")
        print(f"Available regions: {', '.join(TERRAIN_DATA.keys())}")
        return False

    data_info = TERRAIN_DATA[region_key]
    data_dir = get_data_directory()
    dest_path = data_dir / data_info['filename']

    print(f"\n{'='*60}")
    print(f"Downloading: {region_key}")
    print(f"Description: {data_info['description']}")
    print(f"Size: ~{data_info['size_mb']} MB")
    print(f"{'='*60}\n")

    # 이미 파일이 있는지 확인
    if dest_path.exists():
        print(f"  File already exists: {dest_path}")

        # 해시값 검증
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

    # 다운로드 실행
    if not download_file(data_info['url'], dest_path, data_info['size_mb']):
        return False

    # 무결성 검증
    if not verify_file(dest_path, data_info['sha256']):
        print(f"  Removing corrupted file...")
        dest_path.unlink()
        return False

    print(f"\n✓ Successfully downloaded: {dest_path}")
    return True


def list_available_data():
    """사용 가능한 terrain 데이터 목록 출력"""
    print("\nAvailable terrain datasets:")
    print("=" * 60)

    for key, info in TERRAIN_DATA.items():
        print(f"\n  {key}")
        print(f"    Description: {info['description']}")
        print(f"    Size: ~{info['size_mb']} MB")
        print(f"    File: {info['filename']}")

    print("\n" + "=" * 60)


def check_installed_data():
    """설치된 terrain 데이터 확인"""
    data_dir = get_data_directory()

    print("\nInstalled terrain data:")
    print("=" * 60)

    found_any = False
    for key, info in TERRAIN_DATA.items():
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
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python3 download_terrain_data.py <command>")
        print("\nCommands:")
        print("  all           - Download all available terrain data")
        print("  list          - List available terrain datasets")
        print("  check         - Check installed terrain data")
        print("  <region>      - Download specific region (e.g., 'korea')")
        print("\nExamples:")
        print("  python3 download_terrain_data.py korea")
        print("  python3 download_terrain_data.py all")
        return 1

    command = sys.argv[1]

    if command == 'list':
        list_available_data()
        return 0

    elif command == 'check':
        check_installed_data()
        return 0

    elif command == 'all':
        print("Downloading all terrain datasets...")
        success = True
        for region_key in TERRAIN_DATA.keys():
            if not download_terrain(region_key):
                success = False
        return 0 if success else 1

    else:
        # 특정 지역 다운로드
        if download_terrain(command):
            return 0
        else:
            return 1


if __name__ == '__main__':
    sys.exit(main())
