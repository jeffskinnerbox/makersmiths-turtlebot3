---
name: ros2-jazzy-topics-services-actions
description: Implement ROS 2 Jazzy Jalisco communication patterns: publishers, subscribers, services (client/server), and actions (client/server) in Python (rclpy) and C++ (rclcpp). Use this skill when the user asks to send or receive data between nodes, implement request-reply patterns, or create long-running tasks with feedback.
---

This skill covers the three core communication mechanisms in ROS 2 Jazzy: **Topics** (async, many-to-many), **Services** (sync request/reply), and **Actions** (async long-running tasks with feedback and goal cancellation).

## Choosing the Right Mechanism

| Need | Use |
|------|-----|
| Stream sensor data / commands continuously | **Topic** |
| Trigger something and wait for a result (fast) | **Service** |
| Long-running task with progress updates & cancellation | **Action** |

---

## 1. Topics

### Python — Publisher

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MyPublisher(Node):

    def __init__(self):
        super().__init__('my_publisher')
        # QoS depth = history buffer size
        self.publisher_ = self.create_publisher(String, 'my_topic', 10)
        self.timer_ = self.create_timer(0.5, self.timer_callback)
        self.count_ = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello {self.count_}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count_ += 1


def main(args=None):
    rclpy.init(args=args)
    node = MyPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.try_shutdown()
```

### Python — Subscriber

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MySubscriber(Node):

    def __init__(self):
        super().__init__('my_subscriber')
        self.subscription_ = self.create_subscription(
            String, 'my_topic', self.listener_callback, 10)

    def listener_callback(self, msg: String):
        self.get_logger().info(f'Received: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = MySubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.try_shutdown()
```

### C++ — Publisher

```cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class MyPublisher : public rclcpp::Node
{
public:
  MyPublisher() : Node("my_publisher"), count_(0)
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("my_topic", 10);
    timer_ = this->create_timer(500ms, std::bind(&MyPublisher::timer_callback, this));
  }

private:
  void timer_callback()
  {
    auto msg = std_msgs::msg::String();
    msg.data = "Hello " + std::to_string(count_++);
    publisher_->publish(msg);
    RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", msg.data.c_str());
  }

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MyPublisher>());
  rclcpp::shutdown();
  return 0;
}
```

### C++ — Subscriber

```cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class MySubscriber : public rclcpp::Node
{
public:
  MySubscriber() : Node("my_subscriber")
  {
    subscription_ = this->create_subscription<std_msgs::msg::String>(
      "my_topic", 10,
      std::bind(&MySubscriber::listener_callback, this, std::placeholders::_1));
  }

private:
  void listener_callback(const std_msgs::msg::String & msg)
  {
    RCLCPP_INFO(this->get_logger(), "Received: '%s'", msg.data.c_str());
  }

  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MySubscriber>());
  rclcpp::shutdown();
  return 0;
}
```

### QoS Profiles (Jazzy)

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,        # or BEST_EFFORT
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    durability=DurabilityPolicy.VOLATILE,          # or TRANSIENT_LOCAL
)
self.publisher_ = self.create_publisher(String, 'my_topic', qos)
```

---

## 2. Services

### Define or reuse a service type
Use built-in types like `std_srvs/srv/SetBool` or create custom `.srv` files.

**Custom `.srv` file** (`srv/AddTwoInts.srv`):

```
int64 a
int64 b
---
int64 sum
```

Add to `CMakeLists.txt` (C++) or `package.xml` dependency (`rosidl_default_generators`).

### Python — Service Server

```python
from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node


class AddTwoIntsServer(Node):

    def __init__(self):
        super().__init__('add_two_ints_server')
        self.srv_ = self.create_service(
            AddTwoInts, 'add_two_ints', self.handle_request)

    def handle_request(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'{request.a} + {request.b} = {response.sum}')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsServer()
    rclpy.spin(node)
    rclpy.try_shutdown()
```

### Python — Service Client

```python
from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node


class AddTwoIntsClient(Node):

    def __init__(self):
        super().__init__('add_two_ints_client')
        self.client_ = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting...')

    def send_request(self, a: int, b: int):
        request = AddTwoInts.Request()
        request.a = a
        request.b = b
        future = self.client_.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        return future.result()


def main(args=None):
    rclpy.init(args=args)
    client = AddTwoIntsClient()
    result = client.send_request(3, 5)
    client.get_logger().info(f'Result: {result.sum}')
    client.destroy_node()
    rclpy.try_shutdown()
```

### C++ — Service Server

```cpp
#include "example_interfaces/srv/add_two_ints.hpp"
#include "rclcpp/rclcpp.hpp"

using AddTwoInts = example_interfaces::srv::AddTwoInts;

class AddTwoIntsServer : public rclcpp::Node
{
public:
  AddTwoIntsServer() : Node("add_two_ints_server")
  {
    service_ = this->create_service<AddTwoInts>(
      "add_two_ints",
      std::bind(&AddTwoIntsServer::handle_request, this,
        std::placeholders::_1, std::placeholders::_2));
  }

private:
  void handle_request(
    const AddTwoInts::Request::SharedPtr request,
    AddTwoInts::Response::SharedPtr response)
  {
    response->sum = request->a + request->b;
    RCLCPP_INFO(this->get_logger(), "%ld + %ld = %ld",
      request->a, request->b, response->sum);
  }

  rclcpp::Service<AddTwoInts>::SharedPtr service_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<AddTwoIntsServer>());
  rclcpp::shutdown();
  return 0;
}
```

### C++ — Service Client

```cpp
#include "example_interfaces/srv/add_two_ints.hpp"
#include "rclcpp/rclcpp.hpp"

using AddTwoInts = example_interfaces::srv::AddTwoInts;

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("add_two_ints_client");
  auto client = node->create_client<AddTwoInts>("add_two_ints");

  while (!client->wait_for_service(std::chrono::seconds(1))) {
    RCLCPP_INFO(node->get_logger(), "Waiting for service...");
  }

  auto request = std::make_shared<AddTwoInts::Request>();
  request->a = 3;
  request->b = 5;

  auto future = client->async_send_request(request);
  if (rclcpp::spin_until_future_complete(node, future) ==
    rclcpp::FutureReturnCode::SUCCESS)
  {
    RCLCPP_INFO(node->get_logger(), "Result: %ld", future.get()->sum);
  }

  rclcpp::shutdown();
  return 0;
}
```

---

## 3. Actions

Actions use a `.action` file with three sections: Goal / Result / Feedback.

**Example `.action` file** (`action/Fibonacci.action`):

```
int32 order
---
int32[] sequence
---
int32[] partial_sequence
```

### Python — Action Server

```python
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from example_interfaces.action import Fibonacci


class FibonacciServer(Node):

    def __init__(self):
        super().__init__('fibonacci_server')
        self.action_server_ = ActionServer(
            self, Fibonacci, 'fibonacci', self.execute_callback)

    def execute_callback(self, goal_handle):
        self.get_logger().info(f'Executing goal: order={goal_handle.request.order}')

        feedback_msg = Fibonacci.Feedback()
        feedback_msg.partial_sequence = [0, 1]

        for i in range(1, goal_handle.request.order):
            feedback_msg.partial_sequence.append(
                feedback_msg.partial_sequence[-1] + feedback_msg.partial_sequence[-2])
            goal_handle.publish_feedback(feedback_msg)

        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = feedback_msg.partial_sequence
        return result


def main(args=None):
    rclpy.init(args=args)
    node = FibonacciServer()
    rclpy.spin(node)
    rclpy.try_shutdown()
```

### Python — Action Client

```python
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from example_interfaces.action import Fibonacci


class FibonacciClient(Node):

    def __init__(self):
        super().__init__('fibonacci_client')
        self.client_ = ActionClient(self, Fibonacci, 'fibonacci')

    def send_goal(self, order: int):
        goal_msg = Fibonacci.Goal()
        goal_msg.order = order

        self.client_.wait_for_server()
        send_goal_future = self.client_.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected.')
            return
        self.get_logger().info('Goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(f'Feedback: {feedback_msg.feedback.partial_sequence}')

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Result: {result.sequence}')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    client = FibonacciClient()
    client.send_goal(10)
    rclpy.spin(client)
```

---

## 4. Custom Message / Service / Action Types

Add to **package.xml**:

```xml
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

Add to **CMakeLists.txt**:

```cmake
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MyMessage.msg"
  "srv/MyService.srv"
  "action/MyAction.action"
)
```

---

## 5. Jazzy-Specific Gotchas

- **`rclpy.try_shutdown()`** over `rclpy.shutdown()` in Python nodes to avoid double-shutdown errors.
- **Action goal cancellation**: Always check `goal_handle.is_cancel_requested` inside long loops in the server's execute callback.
- **QoS mismatches**: Publisher and subscriber QoS must be compatible (e.g., `RELIABLE` publisher + `BEST_EFFORT` subscriber will fail silently). Use `ros2 topic info -v <topic>` to debug.
- **`spin_until_future_complete`** in clients is blocking — don't call it inside another spin callback; use `add_done_callback` pattern instead for async clients.
- **C++ `ament_target_dependencies`**: Must list all message/service packages (e.g., `example_interfaces`) or you'll get linker errors.
