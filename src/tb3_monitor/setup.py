from setuptools import find_packages, setup

package_name = 'tb3_monitor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jeff',
    maintainer_email='jeff@makersmiths.org',
    description='LiDAR and health monitoring nodes for TurtleBot3',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lidar_monitor = tb3_monitor.lidar_monitor_node:main',
            'health_monitor = tb3_monitor.health_monitor_node:main',
            'mock_battery = tb3_monitor.health_monitor_node:mock_battery_main',
            'tf2_verifier = tb3_monitor.tf2_verifier:main',
        ],
    },
)
