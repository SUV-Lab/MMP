from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('mmp_visualization')
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'mmp.rviz')

    # Declare launch argument for world name
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='dokdo',
        description='World name (tif file name without extension in data directory)'
    )

    return LaunchDescription([
        world_arg,

        # Terrain publisher node
        Node(
            package='mmp_terrain',
            executable='terrain_publisher',
            name='terrain_publisher',
            output='screen',
            parameters=[
                {'world': LaunchConfiguration('world')}
            ]
        ),

        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        ),
    ])
