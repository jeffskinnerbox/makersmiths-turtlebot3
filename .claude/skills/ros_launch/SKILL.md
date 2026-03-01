---
name: ros2-jazzy-launch
description: Create ROS 2 Jazzy Jalisco launch files in Python. Use this skill when the user asks to write a launch file, start multiple nodes together, remap topics, pass parameters, include other launch files, or configure a robot bringup. Covers ros2 launch Python API for Jazzy.
---

This skill guides creation of Python launch files for ROS 2 Jazzy Jalisco. XML and YAML launch formats are supported but **Python launch files are the recommended and most powerful format** — always use Python unless the user explicitly requests otherwise.

## Key Concepts

- Launch files live in a `launch/` directory inside the package.
- They must be installed via `CMakeLists.txt` or `setup.py`.
- The entry point is a `generate_launch_description()` function returning a `LaunchDescription`.

---

## 1. Minimal Python Launch File

**`launch/my_launch.py`**

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_package',
            executable='my_node',
            name='my_node',
            output='screen',
        ),
    ])
```

---

## 2. Installing Launch Files

### Python package (`setup.py`)

```python
import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'my_package'

setup(
    # ...
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Install all launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Install parameter files
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
)
```

### C++ package (`CMakeLists.txt`)

```cmake
install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}/)
```

---

## 3. Common Launch Actions

### Passing Parameters Inline

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_package',
            executable='my_node',
            name='my_node',
            output='screen',
            parameters=[{
                'my_param': 'hello',
                'speed': 1.5,
                'use_sim_time': False,
            }],
        ),
    ])
```

### Loading Parameters from a YAML File

**`config/params.yaml`**:

```yaml
my_node:
  ros__parameters:
    my_param: hello
    speed: 1.5
    use_sim_time: false
```

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory('my_package'), 'config', 'params.yaml')

    return LaunchDescription([
        Node(
            package='my_package',
            executable='my_node',
            name='my_node',
            output='screen',
            parameters=[params_file],
        ),
    ])
```

### Topic Remapping

```python
Node(
    package='my_package',
    executable='my_node',
    remappings=[
        ('input_topic', '/robot/sensor'),
        ('output_topic', '/processed_data'),
    ],
)
```

### Namespace

```python
Node(
    package='my_package',
    executable='my_node',
    namespace='robot1',
    name='my_node',
)
# Node name will be /robot1/my_node
```

---

## 4. Launch Arguments (Runtime Configurability)

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true',
    )

    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='my_robot',
        description='Name of the robot',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')

    my_node = Node(
        package='my_package',
        executable='my_node',
        name='my_node',
        parameters=[{'use_sim_time': use_sim_time}],
        namespace=robot_name,
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        robot_name_arg,
        my_node,
    ])
```

**Run with arguments:**

```bash
ros2 launch my_package my_launch.py use_sim_time:=true robot_name:=robot1
```

---

## 5. Including Other Launch Files

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    other_pkg_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('other_package'),
                'launch', 'other_launch.py'
            )
        ),
        launch_arguments={'use_sim_time': 'true'}.items(),
    )

    return LaunchDescription([
        other_pkg_launch,
    ])
```

---

## 6. Conditional Actions

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='true')
    use_rviz = LaunchConfiguration('use_rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(use_rviz),           # Only launch if use_rviz=true
    )

    headless_node = Node(
        package='my_package',
        executable='headless_monitor',
        condition=UnlessCondition(use_rviz),       # Only launch if use_rviz=false
    )

    return LaunchDescription([
        use_rviz_arg,
        rviz_node,
        headless_node,
    ])
```

---

## 7. Events: On-Process Events & Shutdown

```python
from launch import LaunchDescription
from launch.actions import RegisterEventHandler, EmitEvent, LogInfo
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node


def generate_launch_description():
    my_node = Node(package='my_package', executable='my_node', name='my_node')

    # Shutdown entire launch when my_node exits
    shutdown_on_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=my_node,
            on_exit=[
                LogInfo(msg='my_node exited. Shutting down.'),
                EmitEvent(event=Shutdown()),
            ],
        )
    )

    return LaunchDescription([my_node, shutdown_on_exit])
```

---

## 8. Multiple Nodes — Full Bringup Example

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    use_sim_time = LaunchConfiguration('use_sim_time')

    pkg_share = get_package_share_directory('my_robot_bringup')
    params_file = os.path.join(pkg_share, 'config', 'params.yaml')

    sensor_node = Node(
        package='sensor_pkg',
        executable='sensor_node',
        name='sensor',
        namespace='robot',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
    )

    controller_node = Node(
        package='controller_pkg',
        executable='controller_node',
        name='controller',
        namespace='robot',
        output='screen',
        remappings=[('cmd_vel', '/robot/cmd_vel')],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('nav2_bringup'),
                         'launch', 'navigation_launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    return LaunchDescription([
        use_sim_time_arg,
        sensor_node,
        controller_node,
        nav_launch,
    ])
```

---

## 9. Jazzy-Specific Gotchas

- **Launch file naming convention**: Use `.launch.py` suffix (e.g. `bringup.launch.py`) so glob patterns in `setup.py` catch them cleanly.
- **`get_package_share_directory`** requires the package to be built and sourced — it will raise `PackageNotFoundError` at launch time if not.
- **`LaunchConfiguration` is a substitution**, not a Python string. You cannot use Python `if` on it directly — use `IfCondition` / `UnlessCondition` instead.
- **`output='screen'`** shows node stdout/stderr in the terminal. Use `output='log'` to write only to `~/.ros/log/`.
- **`parameters` list**: Each entry can be a dict or a path string. Multiple entries are merged in order (later values override earlier ones).
- **Namespacing and remapping**: A node's full name is `/<namespace>/<name>`. Always verify with `ros2 node list` after launch.
- **`use_sim_time`**: Must be set as a parameter on every node that uses `/clock` — there is no global setting.
