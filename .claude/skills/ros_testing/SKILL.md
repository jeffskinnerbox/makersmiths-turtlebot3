---
name: ros2-jazzy-testing
description: Write and run tests for ROS 2 Jazzy Jalisco nodes and packages using pytest (Python unit/integration tests) and ros2 launch testing (system-level tests). Use this skill when the user asks to test a ROS 2 node, verify topic output, test a service or action, write unit tests for node logic, or set up a CI-friendly test suite.
---

This skill covers testing ROS 2 Jazzy Jalisco packages at three levels:

1. **Unit tests** — pure Python/C++ logic, no ROS runtime needed
2. **Node integration tests** — spin a real node, check its behavior (pytest + rclpy)
3. **Launch integration tests** — start a full system via launch, validate end-to-end behavior

---

## 0. Test Structure

```
my_package/
├── my_package/
│   └── my_node.py
└── test/
    ├── test_unit.py            # Pure logic tests, no ROS
    ├── test_node.py            # Node integration tests (rclpy)
    └── test_launch.py          # ros2 launch tests
```

---

## 1. Installing Test Dependencies

**`package.xml`**:

```xml
<test_depend>ament_copyright</test_depend>
<test_depend>ament_flake8</test_depend>
<test_depend>ament_pep257</test_depend>
<test_depend>python3-pytest</test_depend>
<test_depend>launch_testing</test_depend>
<test_depend>launch_testing_ros</test_depend>
```

**`CMakeLists.txt`** (C++ or mixed):

```cmake
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_node test/test_node.py)
  ament_add_pytest_test(test_launch test/test_launch.py
    TIMEOUT 60)
endif()
```

**`setup.cfg`** (Python packages — enables pytest discovery):

```ini
[tool:pytest]
junit_family=xunit2
```

---

## 2. Unit Tests (No ROS Runtime)

These test pure logic functions isolated from any Node.

```python
# test/test_unit.py
import pytest
from my_package.utils import compute_distance  # example helper function


def test_distance_zero():
    assert compute_distance(0, 0, 0, 0) == 0.0


def test_distance_positive():
    result = compute_distance(0, 0, 3, 4)
    assert abs(result - 5.0) < 1e-6


def test_distance_negative_coords():
    result = compute_distance(-1, -1, 2, 3)
    assert result > 0
```

Run:

```bash
cd ~/ros2_ws
colcon test --packages-select my_package
colcon test-result --verbose
```

Or directly with pytest:

```bash
pytest src/my_package/test/test_unit.py -v
```

---

## 3. Node Integration Tests (pytest + rclpy)

Spin real nodes in-process; verify published topics, service responses, and parameter behavior.

### 3a. Testing a Publisher

```python
# test/test_node.py
import pytest
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading
import time


@pytest.fixture(scope='module')
def ros_context():
    rclpy.init()
    yield
    rclpy.try_shutdown()


def test_publisher_publishes(ros_context):
    from my_package.my_node import MyPublisher  # import the node class

    received = []

    # Create a helper subscriber node
    helper = rclpy.create_node('test_helper')
    helper.create_subscription(
        String, 'my_topic',
        lambda msg: received.append(msg.data), 10)

    pub_node = MyPublisher()

    # Spin both nodes in a thread briefly
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(helper)
    executor.add_node(pub_node)

    end_time = time.time() + 3.0
    while time.time() < end_time and len(received) < 3:
        executor.spin_once(timeout_sec=0.1)

    executor.shutdown()
    helper.destroy_node()
    pub_node.destroy_node()

    assert len(received) >= 3, f'Expected at least 3 messages, got {len(received)}'
    assert all('Hello' in msg for msg in received)
```

### 3b. Testing a Service

```python
# test/test_service.py
import pytest
import rclpy
from example_interfaces.srv import AddTwoInts
from my_package.add_two_ints_server import AddTwoIntsServer
import time


@pytest.fixture(scope='module')
def ros_context():
    rclpy.init()
    yield
    rclpy.try_shutdown()


def test_add_two_ints_service(ros_context):
    server = AddTwoIntsServer()
    client_node = rclpy.create_node('test_client')
    client = client_node.create_client(AddTwoInts, 'add_two_ints')

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(server)
    executor.add_node(client_node)

    assert client.wait_for_service(timeout_sec=5.0), 'Service not available'

    request = AddTwoInts.Request()
    request.a = 7
    request.b = 3

    future = client.call_async(request)
    end_time = time.time() + 5.0
    while not future.done() and time.time() < end_time:
        executor.spin_once(timeout_sec=0.1)

    assert future.done(), 'Service call timed out'
    assert future.result().sum == 10

    executor.shutdown()
    server.destroy_node()
    client_node.destroy_node()
```

### 3c. Testing Parameters

```python
def test_parameter_declaration(ros_context):
    from my_package.my_node import MyNode

    node = MyNode()
    val = node.get_parameter('my_param').get_parameter_value().string_value
    assert val == 'default_value'
    node.destroy_node()
```

---

## 4. Launch Integration Tests (ros2 launch testing)

System-level tests: start nodes via a launch file, validate behaviors end-to-end.

### 4a. Test Launch File

```python
# test/test_launch.py
import pytest
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.markers
import rclpy
import unittest
from std_msgs.msg import String
import time


# Mark this as a launch test
@pytest.mark.launch_test
@launch_testing.markers.keep_alive
def generate_test_description():
    my_node = launch_ros.actions.Node(
        package='my_package',
        executable='my_node',
        name='my_node',
        output='screen',
    )

    return launch.LaunchDescription([
        my_node,
        # Signal that the test can start
        launch_testing.actions.ReadyToTest(),
    ])


class TestMyNodeOutput(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.try_shutdown()

    def setUp(self):
        self.node = rclpy.create_node('test_listener')

    def tearDown(self):
        self.node.destroy_node()

    def test_receives_messages(self):
        received = []
        self.node.create_subscription(
            String, 'my_topic',
            lambda msg: received.append(msg.data), 10)

        end_time = time.time() + 5.0
        while time.time() < end_time and len(received) < 2:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertGreaterEqual(len(received), 2,
            f'Expected 2+ messages, got {len(received)}')


# Post-shutdown checks (runs after launch is torn down)
@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        # Verify all processes exited cleanly (code 0)
        launch_testing.asserts.assertExitCodes(proc_info)
```

### 4b. Running Launch Tests

```bash
# Via colcon (recommended)
colcon test --packages-select my_package --pytest-args -v

# Directly via pytest
pytest src/my_package/test/test_launch.py -v

# With extra timeout
pytest src/my_package/test/test_launch.py --launch-testing-timeout=30
```

---

## 5. C++ Unit Tests with GTest

```cmake
# CMakeLists.txt
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_my_logic test/test_my_logic.cpp)
  ament_target_dependencies(test_my_logic rclcpp)
  target_include_directories(test_my_logic PRIVATE include)
endif()
```

```cpp
// test/test_my_logic.cpp
#include <gtest/gtest.h>
#include "my_package/my_utils.hpp"

TEST(MyLogicTest, ComputeDistanceZero)
{
  EXPECT_DOUBLE_EQ(compute_distance(0.0, 0.0, 0.0, 0.0), 0.0);
}

TEST(MyLogicTest, ComputeDistancePositive)
{
  EXPECT_NEAR(compute_distance(0.0, 0.0, 3.0, 4.0), 5.0, 1e-6);
}

int main(int argc, char ** argv)
{
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
```

---

## 6. Linting Tests (Auto-included in ament)

`ament_lint_auto` adds automatic linting tests when `BUILD_TESTING` is ON:
- `ament_flake8` — PEP8 compliance
- `ament_pep257` — docstring style
- `ament_copyright` — license header check
- `ament_cppcheck` / `ament_cpplint` — C++ checks

To skip a specific linter:

```cmake
set(ament_cmake_copyright_FOUND TRUE)   # Skip copyright check
set(ament_cmake_cpplint_FOUND TRUE)     # Skip cpplint
ament_lint_auto_find_test_dependencies()
```

---

## 7. Checking Test Results

```bash
# Summary of all tests
colcon test-result

# Verbose with failure details
colcon test-result --verbose

# View raw pytest output
cat log/latest_test/my_package/stdout_stderr.log

# View JUnit XML (for CI)
ls log/latest_test/my_package/*.xml
```

---

## 8. Jazzy-Specific Gotchas

- **`rclpy.init()` can only be called once per process** — use `scope='module'` fixtures or `rclpy.ok()` guards to avoid double-init in multi-test modules.
- **`spin_once` vs `spin`**: In tests, always use `spin_once(timeout_sec=...)` in a loop with a deadline — never blocking `spin()`, which would hang the test.
- **Launch test `ReadyToTest()`** must be included in the `LaunchDescription` returned by `generate_test_description()` — without it, the test will hang waiting for readiness.
- **`keep_alive` marker**: Without `@launch_testing.markers.keep_alive`, the launch will shut down as soon as all initial processes exit, potentially before tests complete.
- **Test isolation**: Each test function should create and destroy its own nodes — shared state between tests causes flakiness.
- **Executor in tests**: For service/action tests, manually spin an executor rather than relying on background threads, to keep tests deterministic.
- **`colcon test` reruns**: Use `colcon test --retest-until-pass 3` for flaky timing-dependent tests in CI.
