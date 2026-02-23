#!/usr/bin/env python3
"""
인터랙티브 맵 추출 도구
- 전체 맵을 보여주고 마우스로 클릭하면 해당 지점 중심으로 정사각형 영역 추출
"""
import sys
import os
import argparse
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import Slider, Button, TextBox
from rasterio.windows import from_bounds


class InteractiveMapExtractor:
    def __init__(self, input_tif, default_size=0.8, output_dir='.'):
        self.input_tif = input_tif
        self.size_deg = default_size
        self.output_dir = output_dir
        self.center_lat = None
        self.center_lon = None
        self.rect = None
        self.output_name = "extracted"

        # TIF 파일 열기
        print(f"Loading {input_tif}...")
        self.src = rasterio.open(input_tif)

        # 전체 맵 읽기 (다운샘플링해서 빠르게)
        scale = 10  # 10픽셀마다 하나씩만 읽기
        self.data = self.src.read(1, out_shape=(
            self.src.height // scale,
            self.src.width // scale
        ))

        # NoData 처리
        self.data = np.where(self.data < -9000, np.nan, self.data)

        # 좌표 범위
        self.bounds = self.src.bounds
        self.lat_min, self.lat_max = self.bounds.bottom, self.bounds.top
        self.lon_min, self.lon_max = self.bounds.left, self.bounds.right

        print(f"Map bounds: lat [{self.lat_min:.2f}, {self.lat_max:.2f}], "
              f"lon [{self.lon_min:.2f}, {self.lon_max:.2f}]")

        self._setup_gui()

    def _setup_gui(self):
        """GUI 설정"""
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        plt.subplots_adjust(left=0.1, bottom=0.25, right=0.9, top=0.95)

        # 맵 표시
        extent = [self.lon_min, self.lon_max, self.lat_min, self.lat_max]
        self.im = self.ax.imshow(self.data, extent=extent,
                                 cmap='terrain', origin='upper',
                                 aspect='auto', interpolation='bilinear')

        self.ax.set_xlabel('Longitude (°)', fontsize=12)
        self.ax.set_ylabel('Latitude (°)', fontsize=12)
        self.ax.set_title('Click to select extraction center | Mouse hover shows preview',
                         fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)

        # 컬러바
        cbar = plt.colorbar(self.im, ax=self.ax)
        cbar.set_label('Elevation (m)', rotation=270, labelpad=20)

        # 크기 슬라이더
        ax_size = plt.axes([0.15, 0.15, 0.65, 0.03])
        self.slider_size = Slider(
            ax_size, 'Size (°)', 0.1, 10.0,
            valinit=self.size_deg, valstep=0.1
        )
        self.slider_size.on_changed(self.update_size)

        # 출력 파일명 입력
        ax_name = plt.axes([0.15, 0.10, 0.3, 0.03])
        self.textbox_name = TextBox(ax_name, 'Output name:',
                                     initial=self.output_name)
        self.textbox_name.on_submit(self.update_name)

        # Extract 버튼
        ax_extract = plt.axes([0.55, 0.10, 0.1, 0.04])
        self.btn_extract = Button(ax_extract, 'Extract',
                                  color='lightgreen', hovercolor='green')
        self.btn_extract.on_clicked(self.extract_region)

        # 상태 텍스트
        self.status_text = self.fig.text(
            0.15, 0.05,
            'Hover mouse to preview | Click to select center | Press Extract to save',
            fontsize=11, color='blue'
        )

        # 마우스 이벤트 연결
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)

    def update_size(self, val):
        """크기 슬라이더 업데이트"""
        self.size_deg = val
        if self.rect:
            self.update_rectangle()

    def update_name(self, text):
        """출력 파일명 업데이트"""
        self.output_name = text

    def on_hover(self, event):
        """마우스 호버 시 미리보기 사각형 표시"""
        if event.inaxes != self.ax:
            return

        lon, lat = event.xdata, event.ydata

        # 미리보기 사각형 업데이트
        if hasattr(self, 'preview_rect') and self.preview_rect:
            try:
                self.preview_rect.remove()
            except (ValueError, AttributeError):
                pass

        half_size = self.size_deg / 2.0
        self.preview_rect = Rectangle(
            (lon - half_size, lat - half_size),
            self.size_deg, self.size_deg,
            fill=False, edgecolor='yellow', linewidth=2,
            linestyle='--', alpha=0.7
        )
        self.ax.add_patch(self.preview_rect)

        # 상태 텍스트 업데이트
        self.status_text.set_text(
            f'Preview: Center ({lat:.2f}°, {lon:.2f}°) | '
            f'Size {self.size_deg}° × {self.size_deg}° '
            f'(~{self.size_deg*111:.0f}km × {self.size_deg*111:.0f}km)'
        )

        self.fig.canvas.draw_idle()

    def on_click(self, event):
        """마우스 클릭 시 중심점 선택"""
        if event.inaxes != self.ax:
            return

        self.center_lon, self.center_lat = event.xdata, event.ydata

        # 기존 사각형 제거
        if self.rect:
            try:
                self.rect.remove()
            except (ValueError, AttributeError):
                pass
            self.rect = None

        # 새 사각형 그리기
        self.update_rectangle()

        # 상태 텍스트 업데이트
        self.status_text.set_text(
            f'Selected: Center ({self.center_lat:.2f}°, {self.center_lon:.2f}°) | '
            f'Size {self.size_deg}° × {self.size_deg}° | '
            f'Press Extract to save as {self.output_name}.tif'
        )
        self.status_text.set_color('green')
        self.status_text.set_fontweight('bold')

        self.fig.canvas.draw()

    def update_rectangle(self):
        """선택 영역 사각형 업데이트"""
        if self.center_lat is None or self.center_lon is None:
            return

        if self.rect:
            try:
                self.rect.remove()
            except (ValueError, AttributeError):
                pass

        half_size = self.size_deg / 2.0
        self.rect = Rectangle(
            (self.center_lon - half_size, self.center_lat - half_size),
            self.size_deg, self.size_deg,
            fill=False, edgecolor='red', linewidth=3, linestyle='-'
        )
        self.ax.add_patch(self.rect)
        self.fig.canvas.draw()

    def extract_region(self, event):
        """선택된 영역 추출"""
        if self.center_lat is None or self.center_lon is None:
            self.status_text.set_text(
                'Error: Click on the map to select a center point first!'
            )
            self.status_text.set_color('red')
            self.status_text.set_fontweight('bold')
            self.fig.canvas.draw()
            return

        # 파일명 충돌 방지
        output_file = os.path.join(self.output_dir, f"{self.output_name}.tif")
        counter = 2
        while os.path.exists(output_file):
            output_file = os.path.join(self.output_dir, f"{self.output_name}_{counter}.tif")
            counter += 1

        print(f"\nExtracting region...")
        print(f"  Center: ({self.center_lat:.2f}°, {self.center_lon:.2f}°)")
        print(f"  Size: {self.size_deg}° × {self.size_deg}°")

        half_size = self.size_deg / 2.0
        min_lat = self.center_lat - half_size
        max_lat = self.center_lat + half_size
        min_lon = self.center_lon - half_size
        max_lon = self.center_lon + half_size

        # 윈도우 계산
        window = from_bounds(min_lon, min_lat, max_lon, max_lat,
                            self.src.transform)
        window = window.round_offsets().round_lengths()

        # 데이터 읽기
        data = self.src.read(1, window=window)

        # Transform 계산
        new_transform = rasterio.transform.from_bounds(
            min_lon, min_lat, max_lon, max_lat,
            window.width, window.height
        )

        # 저장
        profile = self.src.profile.copy()
        profile.update({
            'width': window.width,
            'height': window.height,
            'transform': new_transform
        })

        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(data, 1)

        print(f"✓ Saved to {output_file}")
        print(f"  Size: {window.width} × {window.height} pixels")

        self.status_text.set_text(
            f'✓ Successfully extracted to {output_file} | '
            f'Size: {window.width}×{window.height} pixels'
        )
        self.status_text.set_color('green')
        self.status_text.set_fontweight('bold')
        self.fig.canvas.draw()

    def show(self):
        """GUI 표시"""
        plt.show()

    def __del__(self):
        """정리"""
        if hasattr(self, 'src'):
            self.src.close()


def main():
    parser = argparse.ArgumentParser(
        description='Interactive map extraction tool'
    )
    parser.add_argument(
        '--input',
        default='merged.tif',
        help='Input TIF file (default: merged.tif)'
    )
    parser.add_argument(
        '--size',
        type=float,
        default=0.8,
        help='Default extraction size in degrees (default: 0.8)'
    )
    parser.add_argument(
        '--output-dir',
        default='../src/mmp_terrain/data',
        help='Output directory for extracted files (default: ../src/mmp_terrain/data)'
    )

    args = parser.parse_args()

    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)

    extractor = InteractiveMapExtractor(args.input, args.size, args.output_dir)
    extractor.show()


if __name__ == '__main__':
    main()
