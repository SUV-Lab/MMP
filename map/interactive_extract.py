#!/usr/bin/env python3
import sys
import os
import argparse
import rasterio
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import Slider, Button, TextBox
from rasterio.windows import from_bounds
import threading
import signal
import time


class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        self.canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        cv = self.canvas
        fig = cv.figure
        if self._bg is None:
            self.on_draw(None)
        else:
            cv.restore_region(self._bg)
            self._draw_animated()
            cv.blit(fig.bbox)


class InteractiveMapExtractor:
    def __init__(self, input_tif, default_size=0.8, output_dir='.'):
        self.input_tif = input_tif
        self.size_deg = default_size
        self.output_dir = output_dir
        self.center_lat = None
        self.center_lon = None
        self.rect = None
        self.preview_rect = None
        self.output_name = "extracted"
        self.blit_manager = None
        self._event_connections = []
        self._save_threads = []

        print(f"Loading {input_tif}...")
        self.src = rasterio.open(input_tif)

        scale = 10
        self.data = self.src.read(1, out_shape=(
            self.src.height // scale,
            self.src.width // scale
        ))

        self.data = np.where(self.data < -9000, np.nan, self.data)

        self.bounds = self.src.bounds
        self.lat_min, self.lat_max = self.bounds.bottom, self.bounds.top
        self.lon_min, self.lon_max = self.bounds.left, self.bounds.right

        print(f"Map bounds: lat [{self.lat_min:.2f}, {self.lat_max:.2f}], "
              f"lon [{self.lon_min:.2f}, {self.lon_max:.2f}]")

        self._setup_gui()

    def _setup_gui(self):
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        plt.subplots_adjust(left=0.1, bottom=0.25, right=0.9, top=0.95)

        extent = [self.lon_min, self.lon_max, self.lat_min, self.lat_max]
        self.im = self.ax.imshow(self.data, extent=extent,
                                 cmap='terrain', origin='upper',
                                 aspect='auto', interpolation='bilinear')

        self.ax.set_xlabel('Longitude (°)', fontsize=12)
        self.ax.set_ylabel('Latitude (°)', fontsize=12)
        self.ax.set_title('Click to select extraction center | Mouse hover shows preview',
                         fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)

        cbar = plt.colorbar(self.im, ax=self.ax)
        cbar.set_label('Elevation (m)', rotation=270, labelpad=20)

        self.preview_rect = Rectangle(
            (0, 0), 0, 0,
            fill=False, edgecolor='yellow', linewidth=2,
            linestyle='--', alpha=0.7, visible=False
        )
        self.ax.add_patch(self.preview_rect)

        self.rect = Rectangle(
            (0, 0), 0, 0,
            fill=False, edgecolor='red', linewidth=3,
            linestyle='-', visible=False
        )
        self.ax.add_patch(self.rect)

        ax_size = plt.axes([0.15, 0.15, 0.65, 0.03])
        self.slider_size = Slider(
            ax_size, 'Size (°)', 0.1, 10.0,
            valinit=self.size_deg, valstep=0.1
        )
        self.slider_size.on_changed(self.update_size)

        ax_name = plt.axes([0.15, 0.10, 0.3, 0.03])
        self.textbox_name = TextBox(ax_name, 'Output name:',
                                     initial=self.output_name)
        self.textbox_name.on_submit(self.update_name)

        ax_extract = plt.axes([0.55, 0.10, 0.1, 0.04])
        self.btn_extract = Button(ax_extract, 'Extract',
                                  color='lightgreen', hovercolor='green')
        self.btn_extract.on_clicked(self.extract_region)

        self.status_text = self.fig.text(
            0.15, 0.05,
            'Hover mouse to preview | Click to select center | Press Extract to save',
            fontsize=11, color='blue'
        )

        self.blit_manager = BlitManager(
            self.fig.canvas,
            [self.preview_rect, self.rect, self.status_text]
        )

        cid1 = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        cid2 = self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
        cid3 = self.fig.canvas.mpl_connect('close_event', self.on_close)
        self._event_connections = [cid1, cid2, cid3]

        self.fig.canvas.draw()

    def update_size(self, val):
        self.size_deg = val
        if self.rect and self.rect.get_visible():
            self.update_rectangle()

    def update_name(self, text):
        self.output_name = text

    def on_hover(self, event):
        if event.inaxes != self.ax:
            if self.preview_rect.get_visible():
                self.preview_rect.set_visible(False)
                self.blit_manager.update()
            return

        lon, lat = event.xdata, event.ydata

        half_size = self.size_deg / 2.0
        self.preview_rect.set_bounds(
            lon - half_size,
            lat - half_size,
            self.size_deg,
            self.size_deg
        )
        self.preview_rect.set_visible(True)

        self.status_text.set_text(
            f'Preview: Center ({lat:.2f}°, {lon:.2f}°) | '
            f'Size {self.size_deg}° × {self.size_deg}° '
            f'(~{self.size_deg*111:.0f}km × {self.size_deg*111:.0f}km)'
        )

        self.blit_manager.update()

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        self.center_lon, self.center_lat = event.xdata, event.ydata

        self.update_rectangle()

        self.status_text.set_text(
            f'Selected: Center ({self.center_lat:.2f}°, {self.center_lon:.2f}°) | '
            f'Size {self.size_deg}° × {self.size_deg}° | '
            f'Press Extract to save as {self.output_name}.tif'
        )
        self.status_text.set_color('green')
        self.status_text.set_fontweight('bold')

        self.blit_manager.update()

    def update_rectangle(self):
        if self.center_lat is None or self.center_lon is None:
            return

        half_size = self.size_deg / 2.0
        self.rect.set_bounds(
            self.center_lon - half_size,
            self.center_lat - half_size,
            self.size_deg,
            self.size_deg
        )
        self.rect.set_visible(True)

        self.blit_manager.update()

    def _save_worker(self, output_file, data, profile):
        try:
            with rasterio.open(output_file, 'w', **profile) as dst:
                dst.write(data, 1)
            print(f"✓ Saved to {output_file}")
            print(f"  Size: {profile['width']} × {profile['height']} pixels")

            self.status_text.set_text(
                f'✓ Successfully saved to {output_file} | '
                f'Size: {profile["width"]}×{profile["height"]} pixels'
            )
            self.status_text.set_color('green')
            self.status_text.set_fontweight('bold')
            self.blit_manager.update()
        except Exception as e:
            print(f"✗ Error saving {output_file}: {e}")

            self.status_text.set_text(f'✗ Error saving: {e}')
            self.status_text.set_color('red')
            self.status_text.set_fontweight('bold')
            self.blit_manager.update()

    def extract_region(self, event):
        if self.center_lat is None or self.center_lon is None:
            self.status_text.set_text(
                'Error: Click on the map to select a center point first!'
            )
            self.status_text.set_color('red')
            self.status_text.set_fontweight('bold')
            self.blit_manager.update()
            return

        self.output_name = self.textbox_name.text

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

        window = from_bounds(min_lon, min_lat, max_lon, max_lat,
                            self.src.transform)
        window = window.round_offsets().round_lengths()

        data = self.src.read(1, window=window)

        new_transform = rasterio.transform.from_bounds(
            min_lon, min_lat, max_lon, max_lat,
            window.width, window.height
        )

        profile = self.src.profile.copy()
        profile.update({
            'width': window.width,
            'height': window.height,
            'transform': new_transform
        })

        save_thread = threading.Thread(
            target=self._save_worker,
            args=(output_file, data, profile),
            daemon=True
        )
        save_thread.start()
        self._save_threads.append(save_thread)

        self.status_text.set_text(
            f'💾 Saving to {output_file}... | '
            f'Size: {window.width}×{window.height} pixels'
        )
        self.status_text.set_color('orange')
        self.status_text.set_fontweight('bold')
        self.blit_manager.update()

    def on_close(self, _event):
        self.cleanup()

    def cleanup(self):
        for thread in self._save_threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        self._save_threads.clear()

        for cid in self._event_connections:
            try:
                self.fig.canvas.mpl_disconnect(cid)
            except Exception:
                pass
        self._event_connections.clear()

        if hasattr(self, 'src') and self.src:
            try:
                self.src.close()
            except Exception:
                pass

    def show(self):
        plt.show(block=False)
        plt.pause(0.1)

        try:
            while plt.get_fignums():
                plt.pause(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def __del__(self):
        self.cleanup()


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
    os.makedirs(args.output_dir, exist_ok=True)

    extractor = InteractiveMapExtractor(args.input, args.size, args.output_dir)

    def signal_handler(_sig, _frame):
        print("\n\nInterrupted by user (Ctrl+C)")
        try:
            extractor.cleanup()
            plt.close('all')
        except:
            pass
        os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        extractor.show()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user (Ctrl+C)")
        extractor.cleanup()
        plt.close('all')
        sys.exit(0)


if __name__ == '__main__':
    main()
