# User Guide — Milestone 5: RPi 4 Hardware Deployment

**Version**: 0.1-draft (RPi not yet in hand — hardware sections marked TODO)
**Date**: 2026-03-09
**Stack**: ROS 2 Jazzy, Ubuntu 24.04 Server (arm64), Docker, GL.iNet GL-AXT1800 WiFi

---

## Overview

Milestone 5 deploys the `turtlebot3_robot` container to a Raspberry Pi 4 running on the
physical TurtleBot3 Burger. The `turtlebot3_simulator` container (Gazebo, gamepad, monitoring)
continues to run on the NucBoxM6. Both machines communicate over a GL.iNet travel router.

```
NucBoxM6 (amd64)                    RPi 4 (arm64)
┌─────────────────────────┐         ┌──────────────────────────┐
│ turtlebot3_simulator    │         │ turtlebot3_robot         │
│  Gazebo, Nav2, SLAM     │◄──────► │  ros2 nodes, OpenCR      │
│  gamepad, dashboard     │  WiFi   │  LiDAR, motors           │
└─────────────────────────┘         └──────────────────────────┘
         GL.iNet GL-AXT1800 (SSID "JeffTravelRouter-2.4")
```

Both containers use `network_mode: host` and `ROS_DOMAIN_ID=0`. DDS discovery
bridges the two machines (see [DDS Discovery](#dds-discovery-over-wifi) below).

---

## Part 1: RPi 4 Setup

### 1.1 Flash Ubuntu 24.04 Server (arm64)

1. Download **Ubuntu Server 24.04 LTS** for Raspberry Pi from
   [ubuntu.com/download/raspberry-pi](https://ubuntu.com/download/raspberry-pi)
   — choose the 64-bit (arm64) image.

2. Flash to microSD (≥32 GB, Class 10) using Raspberry Pi Imager or `dd`:

   ```bash
   # On host — replace /dev/sdX with your SD card device
   xzcat ubuntu-24.04-preinstalled-server-arm64+raspi.img.xz | sudo dd of=/dev/sdX bs=4M status=progress
   sync
   ```

3. Before first boot, mount the SD `system-boot` partition and edit `network-config`
   to pre-configure WiFi (cloud-init format):

   ```yaml
   version: 2
   wifis:
     wlan0:
       dhcp4: true
       optional: true
       access-points:
         "JeffTravelRouter-2.4":
           password: "<wifi-password>"
   ```

4. Insert SD, power on RPi. Wait ~2 min for first-boot cloud-init to finish.

5. Find RPi IP via router admin (`192.168.8.1` → DHCP leases) or:

   ```bash
   # From NucBoxM6 on same WiFi
   nmap -sn 192.168.8.0/24 | grep -A2 'Raspberry'
   ```

6. SSH in (default user `ubuntu`, password `ubuntu` — you'll be forced to change it):

   ```bash
   ssh ubuntu@<RPI_IP>
   ```

### 1.2 Install Docker on RPi

```bash
# Update and install prerequisites
sudo apt-get update && sudo apt-get install -y ca-certificates curl

# Add Docker's official GPG key and repo
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu noble stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list

sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu
newgrp docker

# Verify
docker run --rm hello-world
```

### 1.3 Build the Turtlebot Container on RPi

The `Dockerfile.turtlebot` must be updated to `jazzy-sbc-latest` before building
(one-line change from `jazzy-pc-latest`).

```bash
# On RPi — clone the repo
git clone https://github.com/<your-repo>/makersmiths-turtlebot3.git ~/turtlebot3
cd ~/turtlebot3

# Edit Dockerfile.turtlebot: change FROM line to jazzy-sbc-latest
# (or pull the updated image directly if already pushed to a registry)

# Build (first build takes ~20–30 min on RPi — downloads large base image)
docker build -f docker/Dockerfile.turtlebot -t turtlebot3_robot .
```

> **R5 — Memory**: RPi 4 (4 GB) is tight. Monitor during build:
> `watch -n 5 free -h`
> If OOM, add a 2 GB swapfile:
>
> ```bash
> sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
> sudo mkswap /swapfile && sudo swapon /swapfile
> echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
> ```

**Test-gate T5.1a**: `docker build` exits 0 — container builds successfully on RPi.

**Test-gate T5.1b/c**: Run inside the built container:

```bash
docker run --rm turtlebot3_robot which ros2
docker run --rm turtlebot3_robot bash -c \
    "source /opt/ros/jazzy/setup.bash && python3 -c 'import rclpy; print(\"ok\")'"
```

---

## Part 2: Network Configuration

### 2.1 WiFi Setup (GL.iNet GL-AXT1800)

1. Connect GL-AXT1800 to power and join its default network on your laptop.
2. Open router admin at `192.168.8.1` (default credentials on label).
3. Configure WAN uplink if internet is needed; for robot-only use, the LAN is self-contained.
4. Connect both NucBoxM6 and RPi to **SSID "JeffTravelRouter-2.4"** (2.4 GHz for range).
5. Assign static IPs via DHCP reservation in the router admin (recommended):
   - NucBoxM6: e.g., `192.168.8.10`
   - RPi 4: e.g., `192.168.8.20`

Verify connectivity:

```bash
# From NucBoxM6
ping 192.168.8.20   # should reach RPi

# From RPi
ping 192.168.8.10   # should reach NucBoxM6
```

---

## Part 3: DDS Discovery over WiFi

Both approaches require:
- `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (already set in both containers)
- `ROS_DOMAIN_ID=0` (already set in both containers)
- `network_mode: host` (already set in docker-compose.yaml)

### Option A: Multicast (try first — zero config)

Fast-DDS default discovery uses UDP multicast (`239.255.0.1:7400`). If the GL-AXT1800
passes multicast between clients (most consumer routers do), this works with no extra config.

**Test-gate T5.1d**:

```bash
# On RPi — start turtlebot container
docker run -d --network host --name turtlebot3_robot \
    -e RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    -e ROS_DOMAIN_ID=0 \
    turtlebot3_robot sleep infinity

docker exec turtlebot3_robot bash -c \
    "source /opt/ros/jazzy/setup.bash && ros2 run demo_nodes_cpp talker"

# On NucBoxM6 (different terminal)
docker exec turtlebot3_simulator bash -c \
    "source /opt/ros/jazzy/setup.bash && ros2 node list"
# Should show /talker from RPi
```

If `ros2 node list` on NucBoxM6 is empty after 30s, multicast is blocked — use Option B.

### Option B: FastDDS Discovery Server (fallback)

The Discovery Server replaces multicast with a unicast rendezvous point. Run it on
the NucBoxM6 (the more powerful machine).

**Step 1 — Start discovery server on NucBoxM6** (outside or inside simulator container):

```bash
# Find NucBoxM6 WiFi IP
ip addr show | grep 'inet ' | grep '192.168.8'
# e.g., 192.168.8.10

# Start FastDDS Discovery Server on port 11811
# Inside simulator container:
docker exec turtlebot3_simulator bash -c \
    "source /opt/ros/jazzy/setup.bash && \
     fastdds discovery -i 0 -l 192.168.8.10 -p 11811"
```

**Step 2 — Set `ROS_DISCOVERY_SERVER` on both machines** before starting ROS nodes:

On NucBoxM6 `docker-compose.yaml` (simulator service environment):

```yaml
environment:
  ROS_DISCOVERY_SERVER: "192.168.8.10:11811"
```

On RPi, run the container with the env var:

```bash
docker run -d --network host --name turtlebot3_robot \
    -e RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    -e ROS_DOMAIN_ID=0 \
    -e ROS_DISCOVERY_SERVER="192.168.8.10:11811" \
    turtlebot3_robot sleep infinity
```

> **Note**: When `ROS_DISCOVERY_SERVER` is set, Fast-DDS switches to super-client
> mode automatically — no multicast is used. All nodes find each other via the server.
> The discovery server process must be running before any nodes start.

**Step 3 — Verify**:

```bash
# On NucBoxM6
docker exec turtlebot3_simulator bash -c \
    "source /opt/ros/jazzy/setup.bash && ros2 node list"
# Should list nodes from both machines
```

> **D8 Decision**: Try Option A first when RPi arrives. Record result in the
> Decisions Log. If multicast fails, apply Option B and update `docker-compose.yaml`
> with the hardcoded NucBoxM6 WiFi IP.

---

## Part 4: Integration Demo

Once DDS discovery works (T5.1d passes):

**Terminal 1 — NucBoxM6: start simulation and dashboard**

```bash
sg docker -c "bash scripts/run_docker.sh"
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup sim_bringup.launch.py headless:=true
```

**Terminal 2 — NucBoxM6: gamepad**

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup gamepad.launch.py
```

**Terminal 3 — NucBoxM6: dashboard**

```bash
bash scripts/tmux_dashboard.sh
```

**RPi (SSH)**: the turtlebot container runs the hardware drivers. Physical robot should
respond to `/cmd_vel` commands published by the gamepad on NucBoxM6.

**Test-gates**:
- T5.2a: `ros2 node list` on NucBoxM6 shows RPi nodes
- T5.2b: Gamepad on NucBoxM6 moves physical robot (hold RB + right stick)
- T5.2c: `ros2 topic echo /scan` on NucBoxM6 shows real LiDAR data
- T5.2d: `ros2 launch tb3_bringup wanderer.launch.py` → robot avoids physical walls

---

## Troubleshooting

**`ros2 node list` on NucBoxM6 shows nothing from RPi**

1. Confirm both machines are on "JeffTravelRouter-2.4" and can ping each other.
2. Confirm `ROS_DOMAIN_ID=0` on both.
3. Try Option B (Discovery Server) if Option A (multicast) fails (R4).
4. Check firewall: `sudo ufw status` — disable or allow UDP 7400, 7401, 11811.

**Container build OOM on RPi**

Add swap (see [1.3](#13-build-the-turtlebot-container-on-rpi)) and retry.
Monitor with `watch -n 2 'free -h && docker stats --no-stream'` during build.

**Robot doesn't move when gamepad pressed**

Confirm `/cmd_vel` is published on NucBoxM6 and bridged to RPi:

```bash
# On NucBoxM6
docker exec turtlebot3_simulator bash -c \
    "source /opt/ros/jazzy/setup.bash && ros2 topic echo /cmd_vel"
```

If no data: check gamepad launch (e-stop may be active — press A to clear).
If data present but robot silent: check DDS discovery (T5.1d).

**`/scan` shows no data on NucBoxM6**

The LiDAR driver runs inside the RPi container. Verify it's running:

```bash
# On RPi
docker exec turtlebot3_robot bash -c \
    "source /opt/ros/jazzy/setup.bash && ros2 node list"
```

---

## Automated Tests

M5 tests require hardware — they cannot run headless.

```bash
# TODO: add after hardware is verified
# bash scripts/run_tests.sh m5
```

See `scripts/run_tests.sh` — `m5` subcommand will be added during Phase 5.2
after all test-gates are verified on hardware.
