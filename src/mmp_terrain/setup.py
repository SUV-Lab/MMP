from setuptools import setup
import os
from glob import glob

package_name = 'mmp_terrain'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'data'), glob('data/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lim',
    maintainer_email='lim@todo.todo',
    description='Terrain model publisher for MMP',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'terrain_publisher = mmp_terrain.terrain_publisher:main',
        ],
    },
)
