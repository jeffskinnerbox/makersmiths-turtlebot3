graph TB
    subgraph host["Host Machine (Ubuntu 24.04)"]
        F310[/"F310 Gamepad\n/dev/input/js0"/]
    end

    subgraph sim_container["Docker: turtlebot3_simulator\nosrf/ros:jazzy-desktop-full · network_mode: host · Fast-DDS · GZ_IP=127.0.0.1"]

        subgraph gz["Gazebo Harmonic (gz sim)"]
            GZ_SIM["gz server\nPhysics + Sensors"]
            GZ_GUI["gz GUI client\n(headless:=false only)"]
        end

        subgraph bridge_layer["ROS ↔ Gazebo Bridge"]
            BRIDGE["ros_gz_bridge\nbridge_params.yaml"]
            RSP["robot_state_publisher\nURDF → /tf_static"]
        end

        subgraph bringup["tb3_bringup (launch orchestration)"]
            L_SIM["sim_bringup.launch.py\nsim_house.launch.py"]
            L_GAMEPAD["gamepad.launch.py"]
            L_WANDER["wanderer.launch.py"]
            L_SLAM["slam.launch.py"]
            L_NAV2["nav2.launch.py"]
            L_DEMO["capability_demo.launch.py"]
            L_TELEOP["teleop.launch.py"]
        end

        subgraph monitor["tb3_monitor"]
            LIDAR_MON["lidar_monitor\n/scan → /closest_obstacle\n@ 5 Hz"]
            HEALTH["health_monitor\n/battery_state + /imu → log"]
            MOCK_BAT["mock_battery\n/battery_state @ 1 Hz"]
        end

        subgraph controller["tb3_controller"]
            JOY["joy_node\n/dev/input → /joy @ 20 Hz"]
            TTJ["teleop_twist_joy\n/joy → /cmd_vel_raw"]
            GM["gamepad_manager\n/joy + /cmd_vel_raw → /cmd_vel\ne-stop gating (B/A/Y)"]
            WANDER["wanderer\n/scan + /estop → /cmd_vel\nreactive obstacle avoidance"]
            PATROL["patrol\n/estop + Nav2 → waypoints"]
            SCAN_ACT["scan_action_server\n/tb3_scan_360 action"]
            TTK["teleop_twist_keyboard\n→ /cmd_vel (TTY)"]
        end

        subgraph autonomous["Autonomous Stack"]
            SLAM["slam_toolbox\nonline_async\n/scan → /map + map→odom TF"]
            NAV2["Nav2 Stack\nbt_navigator + DWB planner\n/navigate_to_pose action"]
        end
    end

    subgraph robot_container["Docker: turtlebot3_robot\nrobotis/turtlebot3:jazzy-sbc-latest (RPi4 arm64)\n[Phase 5 — hardware deployment]"]
        HW_TB3["TurtleBot3 Burger\nHardware + OpenCR"]
    end

    %% Hardware input
    F310 -->|"/dev/input bind-mount"| JOY

    %% Launch file relationships
    L_SIM -.->|starts| GZ_SIM
    L_SIM -.->|starts| BRIDGE
    L_SIM -.->|starts| RSP
    L_GAMEPAD -.->|starts| JOY
    L_GAMEPAD -.->|starts| TTJ
    L_GAMEPAD -.->|starts| GM
    L_WANDER -.->|starts| LIDAR_MON
    L_WANDER -.->|starts| WANDER
    L_SLAM -.->|starts| SLAM
    L_NAV2 -.->|starts| NAV2
    L_DEMO -.->|starts| SLAM & NAV2 & LIDAR_MON
    L_DEMO -.->|mode:=patrol| PATROL
    L_DEMO -.->|mode:=wanderer| WANDER
    L_TELEOP -.->|starts| TTK

    %% Gazebo internal
    GZ_SIM --> GZ_GUI

    %% Bridge: Gazebo → ROS
    GZ_SIM <-->|"gz-transport\n(loopback)"| BRIDGE
    BRIDGE -->|"/scan LaserScan"| LIDAR_MON
    BRIDGE -->|"/scan LaserScan"| WANDER
    BRIDGE -->|"/scan LaserScan"| SLAM
    BRIDGE -->|"/odom Odometry"| SCAN_ACT
    BRIDGE -->|"/imu Imu"| HEALTH
    BRIDGE -->|"/clock Clock"| autonomous
    BRIDGE -->|"/tf TFMessage"| autonomous

    %% Bridge: ROS → Gazebo
    GM -->|"/cmd_vel Twist"| BRIDGE
    WANDER -->|"/cmd_vel Twist"| BRIDGE
    NAV2 -->|"/cmd_vel Twist"| BRIDGE
    TTK -->|"/cmd_vel Twist"| BRIDGE

    %% Gamepad chain
    JOY -->|"/joy Joy"| TTJ
    JOY -->|"/joy Joy"| GM
    TTJ -->|"/cmd_vel_raw Twist"| GM

    %% E-stop signal
    GM -->|"/estop Bool\nRELIABLE+TRANSIENT_LOCAL"| WANDER
    GM -->|"/estop Bool"| PATROL

    %% Monitoring
    MOCK_BAT -->|"/battery_state BatteryState"| HEALTH
    LIDAR_MON -->|"/closest_obstacle Float32"| HEALTH

    %% SLAM → Nav2
    SLAM -->|"/map OccupancyGrid"| NAV2
    SLAM -->|"map→odom TF"| NAV2

    %% Nav2 → Patrol
    PATROL -->|"/navigate_to_pose action"| NAV2

    %% Hardware (Phase 5)
    BRIDGE <-.->|"WiFi · DDS · Fast-DDS\n(Phase 5)"| HW_TB3

    %% Styles
    classDef launchFile fill:#2d4a6e,stroke:#5b8dd9,color:#fff
    classDef monitor fill:#2d6e3e,stroke:#5bd96e,color:#fff
    classDef controller fill:#6e2d2d,stroke:#d95b5b,color:#fff
    classDef gazebo fill:#4a3a6e,stroke:#9b7dd9,color:#fff
    classDef autonomous fill:#6e5a2d,stroke:#d9b45b,color:#fff
    classDef future fill:#444,stroke:#888,color:#aaa,stroke-dasharray:5

    class L_SIM,L_GAMEPAD,L_WANDER,L_SLAM,L_NAV2,L_DEMO,L_TELEOP launchFile
    class LIDAR_MON,HEALTH,MOCK_BAT monitor
    class JOY,TTJ,GM,WANDER,PATROL,SCAN_ACT,TTK controller
    class GZ_SIM,GZ_GUI,BRIDGE,RSP gazebo
    class SLAM,NAV2 autonomous
    class robot_container,HW_TB3 future
