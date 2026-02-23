#!/usr/bin/env python3
"""
중심점과 크기를 지정해서 정사각형 영역 추출
"""
import argparse
import rasterio
from rasterio.windows import from_bounds
import numpy as np


def extract_centered_region(input_tif, output_tif, center_lat, center_lon, size_deg):
    """
    중심점 기준으로 정사각형 영역 추출

    Args:
        input_tif: 입력 TIF 파일
        output_tif: 출력 TIF 파일
        center_lat: 중심 위도
        center_lon: 중심 경도
        size_deg: 한 변의 크기 (도 단위)
    """
    half_size = size_deg / 2.0

    min_lat = center_lat - half_size
    max_lat = center_lat + half_size
    min_lon = center_lon - half_size
    max_lon = center_lon + half_size

    print(f"\n추출 영역:")
    print(f"  중심점: 위도 {center_lat}°, 경도 {center_lon}°")
    print(f"  크기: {size_deg}° x {size_deg}°")
    print(f"  범위: 위도 [{min_lat:.2f}, {max_lat:.2f}], 경도 [{min_lon:.2f}, {max_lon:.2f}]")

    with rasterio.open(input_tif) as src:
        # 윈도우 계산
        window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
        window = window.round_offsets().round_lengths()

        # 데이터 읽기
        data = src.read(1, window=window)

        # Transform 계산
        pixel_size = src.transform.a
        new_transform = rasterio.transform.from_bounds(
            min_lon, min_lat, max_lon, max_lat,
            window.width, window.height
        )

        # 출력 파일 저장
        profile = src.profile.copy()
        profile.update({
            'width': window.width,
            'height': window.height,
            'transform': new_transform
        })

        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(data, 1)

        print(f"\n저장 완료: {output_tif}")
        print(f"  크기: {window.width} x {window.height} 픽셀")


def main():
    parser = argparse.ArgumentParser(description='중심점 기준 정사각형 영역 추출')
    parser.add_argument('--input', required=True, help='입력 TIF 파일')
    parser.add_argument('--output', required=True, help='출력 TIF 파일')
    parser.add_argument('--lat', type=float, required=True, help='중심 위도')
    parser.add_argument('--lon', type=float, required=True, help='중심 경도')
    parser.add_argument('--size', type=float, required=True, help='한 변의 크기 (도)')

    args = parser.parse_args()

    extract_centered_region(
        args.input,
        args.output,
        args.lat,
        args.lon,
        args.size
    )


if __name__ == '__main__':
    main()
