import rasterio
import numpy as np
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from grid_map_msgs.msg import GridMap
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, Header
from ament_index_python.packages import get_package_share_directory
import os


TARGET_CELL_SIZE_M = 500.0
TARGET_SCALE = 3

class TerrainPublisher(Node):
    def __init__(self):
        super().__init__('terrain_publisher')
        self.get_logger().info('Terrain publisher initializing...')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            depth=1
        )
        self.pub = self.create_publisher(GridMap, '/terrain/grid_map', qos)
        self.get_logger().info('Publisher created on /terrain/grid_map with TRANSIENT_LOCAL QoS')

        self.get_logger().info('Loading terrain data...')
        grid_map = self.load_tif()

        self.pub.publish(grid_map)
        self.get_logger().info('Terrain GridMap published successfully')
        self.get_logger().info('Node will keep running to serve TRANSIENT_LOCAL subscribers')

    def load_tif(self):
        """TIF -> GridMap msg"""
        self.declare_parameter('world', 'dokdo')
        world_name = self.get_parameter('world').get_parameter_value().string_value

        pkg_share = get_package_share_directory('mmp_terrain')
        tif_path = os.path.join(pkg_share, 'data', f'{world_name}.tif')

        if not os.path.exists(tif_path):
            error_msg = f"""
            ================================================================================
            ERROR: Terrain data file not found!
            Path: {tif_path}

            Please download the terrain data first:

            1. Navigate to the mmp_terrain package:
               cd src/mmp_terrain

            2. Run the download script:
               python3 scripts/download_terrain_data.py korea

            Or download all available datasets:
               python3 scripts/download_terrain_data.py all

            For more information, see the README in mmp_terrain package.
            ================================================================================
            """
            self.get_logger().error(error_msg)
            raise FileNotFoundError(f"Terrain data not found at {tif_path}")

        self.get_logger().info(f'Opening {tif_path}...')
        with rasterio.open(tif_path) as src:
            self.get_logger().info(f'TIF shape: {src.width} x {src.height}')
            self.get_logger().info(f'CRS: {src.crs}')
            elevation = src.read(1).astype(np.float32)
            transform = src.transform
            resolution_deg = transform.a

            bounds = src.bounds
            lat_center = (bounds.top + bounds.bottom) / 2.0
            resolution_m = resolution_deg * math.pi / 180.0 * 6371000 * math.cos(math.radians(lat_center))
            self.get_logger().info(f'Resolution: {resolution_deg}deg = {resolution_m:.2f}m (lat_center={lat_center:.2f})')

        scale = TARGET_SCALE
        elevation = elevation[::scale, ::scale]

        elevation_raw = np.where(elevation < -9000, np.nan, elevation).astype(np.float32)
        elevation = np.where(elevation_raw <= 0, np.nan, elevation_raw)

        # valid_rows = np.where(~np.all(np.isnan(elevation), axis=1))[0]
        # valid_cols = np.where(~np.all(np.isnan(elevation), axis=0))[0]
        # row_min, row_max = valid_rows[0], valid_rows[-1] + 1
        # col_min, col_max = valid_cols[0], valid_cols[-1] + 1
        # elevation = elevation[row_min:row_max, col_min:col_max]

        rows, cols = elevation.shape
        self.get_logger().info(f'Cropped shape: {rows} x {cols}')
        self.get_logger().info(f'Elevation range: {np.nanmin(elevation):.1f}m ~ {np.nanmax(elevation):.1f}m')
        self.get_logger().info(f'NaN count: {np.isnan(elevation).sum()}')

        actual_cell_size = resolution_m * scale
        scale_factor = actual_cell_size / TARGET_CELL_SIZE_M
        self.get_logger().info(f'Actual cell size: {actual_cell_size:.1f}m | Target cell size: {TARGET_CELL_SIZE_M}m | Scale factor: {scale_factor:.4f}')
        self.get_logger().info('Calculating hillshade...')
        hillshade = self.calculate_hillshade(elevation, actual_cell_size)
        self.get_logger().info(f'Hillshade range: {np.nanmin(hillshade):.2f} ~ {np.nanmax(hillshade):.2f}')

        self.get_logger().info('Creating water layer with depth gradient...')
        water = self.create_water_layer(elevation_raw, actual_cell_size)
        water_count = np.sum(~np.isnan(water))
        self.get_logger().info(f'Water cells: {water_count}')

        msg = GridMap()
        msg.header = Header()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.info.resolution = float(scale_factor)
        msg.info.length_x = float(cols * msg.info.resolution)
        msg.info.length_y = float(rows * msg.info.resolution)
        msg.info.pose.position.x = msg.info.length_x / 2.0
        msg.info.pose.position.y = msg.info.length_y / 2.0
        msg.info.pose.orientation.w = 1.0
        self.get_logger().info(f'Map size (grid): {cols} x {rows} cells')
        self.get_logger().info(f'Map size (actual): {cols * actual_cell_size / 1000:.1f}km x {rows * actual_cell_size / 1000:.1f}km')

        msg.layers = ['elevation', 'hillshade', 'water']

        elevation_scaled = elevation / TARGET_CELL_SIZE_M
        elevation_data = elevation_scaled.flatten(order='F').tolist()

        elevation_layer = Float32MultiArray()
        elevation_layer.layout.dim.append(MultiArrayDimension(label='column_index', size=cols, stride=cols * rows))
        elevation_layer.layout.dim.append(MultiArrayDimension(label='row_index', size=rows, stride=rows))
        elevation_layer.data = elevation_data

        hillshade_data = hillshade.flatten(order='F').tolist()

        hillshade_layer = Float32MultiArray()
        hillshade_layer.layout.dim.append(MultiArrayDimension(label='column_index', size=cols, stride=cols * rows))
        hillshade_layer.layout.dim.append(MultiArrayDimension(label='row_index', size=rows, stride=rows))
        hillshade_layer.data = hillshade_data

        water_data = water.flatten(order='F').tolist()

        water_layer = Float32MultiArray()
        water_layer.layout.dim.append(MultiArrayDimension(label='column_index', size=cols, stride=cols * rows))
        water_layer.layout.dim.append(MultiArrayDimension(label='row_index', size=rows, stride=rows))
        water_layer.data = water_data

        msg.data = [elevation_layer, hillshade_layer, water_layer]

        self.get_logger().info(f'GridMap created: {len(elevation_data)} data points, 3 layers (elevation, hillshade, water)')
        return msg

    def create_water_layer(self, elevation_raw, cell_size):
        is_water = elevation_raw <= 0
        water = np.where(is_water, 0.5, np.nan)

        return water.astype(np.float32)

    def calculate_hillshade(self, elevation, cell_size, azimuth=315, altitude=45):
        fy, fx = np.gradient(elevation, cell_size)

        slope = np.arctan(np.sqrt(fx**2 + fy**2))
        aspect = np.arctan2(-fy, fx)

        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)

        hillshade = 255.0 * (
            (np.cos(altitude_rad) * np.cos(slope)) +
            (np.sin(altitude_rad) * np.sin(slope) * np.cos(azimuth_rad - aspect))
        )

        hillshade = np.clip(hillshade, 0, 255)

        hillshade = np.where(np.isnan(elevation), np.nan, hillshade)

        return hillshade.astype(np.float32)


def main():
    print('Initializing rclpy...')
    rclpy.init()

    print('Creating TerrainPublisher node...')
    node = TerrainPublisher()

    print('Spinning node...')
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
