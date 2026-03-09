from setuptools import find_packages, setup

package_name = 'tb3_controller'

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
    description='Gamepad controller and autonomous capabilities for TurtleBot3',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gamepad_manager = tb3_controller.gamepad_manager_node:main',
            'wanderer = tb3_controller.wanderer_node:main',
            'patrol = tb3_controller.patrol_node:main',
            'scan_action_server = tb3_controller.scan_action_server:main',
        ],
    },
)
