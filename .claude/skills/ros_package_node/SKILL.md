---
name: ros2-jazzy-package-node
description: Create ROS 2 Jazzy Jalisco packages and nodes in Python (rclpy) or C++ (rclcpp). Use this skill when the user asks to create a ROS 2 package, node, publisher, subscriber, or any basic ROS 2 component. Covers colcon build, package.xml, CMakeLists.txt, and setup.py conventions for Jazzy.
---

This skill guides creation of well-structured ROS 2 Jazzy Jalisco packages and nodes in Python and C++. Follow these conventions precisely to ensure compatibility with Jazzy's ament build system and colcon.

## Pre-Flight: Environment Assumptions

- ROS 2 Jazzy is sourced: `source /opt/ros/jazzy/setup.bash`
- Workspace exists at `~/ros2_ws/src/` (or user-specified path)
- `colcon` and `ament` tools are available

---

## 1. Creating a Package

### Python Package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  --node-name <node_name> <package_name>
```

**Resulting structure:**

```
<package_name>/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/<package_name>
└── <package_name>/
    ├── __init__.py
    └── <node_name>.py
```

### C++ Package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
  --node-name <node_name> <package_name>
```

**Resulting structure:**

```
<package_name>/
├── CMakeLists.txt
├── package.xml
├── include/<package_name>/
└── src/
    └── <node_name>.cpp
```

---

## 2. package.xml — Required Fields for Jazzy

Always use **format 3**. Jazzy uses `ament_cmake` or `ament_python` as build type.

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_package</name>
  <version>0.0.1</version>
  <description>Brief description</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <!-- Python build -->
  <buildtool_depend>ament_python</buildtool_depend>

  <!-- OR C++ build -->
  <!-- <buildtool_depend>ament_cmake</buildtool_depend> -->

  <depend>rclpy</depend>           <!-- Python -->
  <!-- <depend>rclcpp</depend> -->  <!-- C++ -->

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
    <!-- OR: <build_type>ament_cmake</build_type> -->
  </export>
</package>
```

---

## 3. Python Node Boilerplate

**`<package_name>/<node_name>.py`**

```python
import rclpy
from rclpy.node import Node


class MyNode(Node):

    def __init__(self):
        super().__init__('my_node')
        self.get_logger().info('MyNode has started.')

        # Declare and read parameters
        self.declare_parameter('my_param', 'default_value')
        my_param = self.get_parameter('my_param').get_parameter_value().string_value
        self.get_logger().info(f'Parameter: {my_param}')

        # Timer example (period in seconds)
        self.timer_ = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        self.get_logger().info('Timer fired.')


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
```

**`setup.py`** — register the entry point:

```python
from setuptools import find_packages, setup

package_name = 'my_package'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@email.com',
    description='Description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'my_node = my_package.my_node:main',
        ],
    },
)
```

---

## 4. C++ Node Boilerplate

**`src/<node_name>.cpp`**

```cpp
#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"

using namespace std::chrono_literals;

class MyNode : public rclcpp::Node
{
public:
  MyNode()
  : Node("my_node")
  {
    RCLCPP_INFO(this->get_logger(), "MyNode has started.");

    // Declare and read parameter
    this->declare_parameter("my_param", "default_value");
    auto my_param = this->get_parameter("my_param").as_string();
    RCLCPP_INFO(this->get_logger(), "Parameter: %s", my_param.c_str());

    // Timer example
    timer_ = this->create_timer(1s, std::bind(&MyNode::timer_callback, this));
  }

private:
  void timer_callback()
  {
    RCLCPP_INFO(this->get_logger(), "Timer fired.");
  }

  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<MyNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
```

**`CMakeLists.txt`** — minimal correct version for Jazzy:

```cmake
cmake_minimum_required(VERSION 3.8)
project(my_package)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(my_node src/my_node.cpp)
ament_target_dependencies(my_node rclcpp)

install(TARGETS my_node
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```

---

## 5. Building & Running

```bash
# From workspace root
cd ~/ros2_ws
colcon build --packages-select <package_name>
source install/setup.bash

# Run the node
ros2 run <package_name> <node_name>

# Run with parameter override
ros2 run <package_name> <node_name> --ros-args -p my_param:=hello
```

### Useful colcon flags
- `--symlink-install` — Python: no rebuild needed after editing source
- `--cmake-args -DCMAKE_BUILD_TYPE=Release` — C++: optimized build
- `--event-handlers console_direct+` — verbose output

---

## 6. Common Jazzy-Specific Gotchas

- **Python executable permissions**: `setup.cfg` must contain `[develop] script_dir=$base/lib/<pkg>` and `[install] install_scripts=$base/lib/<pkg>` — the `ros2 pkg create` template sets this automatically.
- **C++ include paths**: Always use `#include "rclcpp/rclcpp.hpp"` (lowercase, with quotes), not angle brackets.
- **ament_target_dependencies vs target_link_libraries**: Prefer `ament_target_dependencies()` for ROS packages; use `target_link_libraries()` only for non-ROS system libs.
- **Parameter typing**: In Jazzy, `get_parameter().as_string()` (C++) and `.get_parameter_value().string_value` (Python) are the correct accessors.
- **Node naming**: Use `snake_case` for node names and topic names; `CamelCase` for class names.
- **Lifecycle nodes**: If the node needs managed states (configure/activate/deactivate), inherit from `rclcpp_lifecycle::LifecycleNode` (C++) or `rclpy.lifecycle.Node` (Python) instead.
