#!/usr/bin/env bash
# run_tests.sh — TurtleBot3 test runner
# Usage: bash scripts/run_tests.sh [m1|m2|m3|all] [--gui]
#
# Subcommands: m1  Milestone 1 (Docker simulation environment)
#              m2  Milestone 2 (Gamepad control) — TODO
#              m3  Milestone 3 (Autonomous capabilities) — TODO
#              all Run all available milestones (default)
#
# Flags: --gui  Enable GUI tests (requires xhost +local:docker; some tests are manual)
#
# G1:  prefix docker commands with sg docker -c until fresh login
# G4:  ros2 topic list hangs; tests use ros2 topic echo/info per specific topic instead
# G13: sim tests run headless by default; --gui launches Gazebo GUI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# ── Argument parsing ──────────────────────────────────────────────────────────
MILESTONE="all"
GUI=false

for arg in "$@"; do
    case $arg in
        m1|m2|m3|all) MILESTONE=$arg ;;
        --gui) GUI=true ;;
        -h|--help)
            sed -n '2,10p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0

_pass() { echo -e "  ${GREEN}PASS${NC}  $1"; ((TOTAL_PASS++)) || true; }
_fail() { echo -e "  ${RED}FAIL${NC}  $1"; ((TOTAL_FAIL++)) || true; }
_skip() { echo -e "  ${YELLOW}SKIP${NC}  $1"; ((TOTAL_SKIP++)) || true; }
_head() { echo -e "\n${BLUE}▶ $1${NC}"; }

# Run a command silently; pass/fail based on exit code
run_test() {
    local name="$1"; shift
    if "$@" > /tmp/tb3_test_out.txt 2>&1; then
        _pass "$name"
    else
        _fail "$name  ($(tail -1 /tmp/tb3_test_out.txt))"
    fi
}

# Run a command inside the simulator container (with ROS sourced)
sim_exec() {
    docker exec turtlebot3_simulator bash -c \
        "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash 2>/dev/null || true && $*"
}

# ── Milestone 1 ───────────────────────────────────────────────────────────────
run_m1() {
    _head "Milestone 1: Docker Simulation Environment"

    # ── Container health ──────────────────────────────────────────────────────
    echo "  Container health:"

    run_test "T1.1b  ros2 CLI in simulator" \
        docker exec turtlebot3_simulator which ros2

    run_test "T1.1c  ros2 CLI in robot" \
        docker exec turtlebot3_robot which ros2

    run_test "T1.1d  rclpy importable in simulator" \
        docker exec turtlebot3_simulator bash -c \
            "source /opt/ros/jazzy/setup.bash && python3 -c 'import rclpy'"

    # ── Workspace build ───────────────────────────────────────────────────────
    echo "  Workspace:"

    run_test "T1.2a  colcon build (tb3_bringup)" \
        docker exec turtlebot3_simulator bash -c \
            "source /opt/ros/jazzy/setup.bash && cd ~/ros2_ws && colcon build --event-handlers console_direct-"

    # ── Bridge config (static check, no Gazebo needed) ────────────────────────
    echo "  Config:"

    run_test "T1.3d  bridge_params.yaml uses geometry_msgs/msg/Twist for /cmd_vel" bash -c \
        "grep -A4 'ros_topic_name: \"/cmd_vel\"' \
            src/tb3_bringup/config/bridge_params.yaml | \
            grep -q 'geometry_msgs/msg/Twist'"

    # ── Unit tests ────────────────────────────────────────────────────────────
    echo "  Unit tests (pytest):"

    run_test "T1.4u  pytest tb3_bringup" \
        docker exec turtlebot3_simulator bash -c \
            "source /opt/ros/jazzy/setup.bash && cd ~/ros2_ws && \
             python3 -m pytest src/tb3_bringup/test/ -q --tb=short 2>&1"

    # ── Simulation (headless) ─────────────────────────────────────────────────
    echo "  Simulation (headless):"

    local launch_results
    launch_results=$(docker exec turtlebot3_simulator bash -c "
        source /opt/ros/jazzy/setup.bash
        source ~/ros2_ws/install/setup.bash 2>/dev/null || true
        ros2 launch tb3_bringup sim_bringup.launch.py headless:=true > /tmp/sim.log 2>&1 &
        LPID=\$!
        sleep 15

        # T1.3a: gz topics
        gz topic -l 2>/dev/null | grep -q '/world/' \
            && echo 'T1.3a:PASS' || echo 'T1.3a:FAIL'

        # T1.3b: /clock
        timeout 5 ros2 topic echo /clock --once > /dev/null 2>&1 \
            && echo 'T1.3b:PASS' || echo 'T1.3b:FAIL'

        # T1.3c: /scan
        timeout 8 ros2 topic echo /scan --once > /dev/null 2>&1 \
            && echo 'T1.3c_scan:PASS' || echo 'T1.3c_scan:FAIL'

        # T1.3c: /odom
        timeout 8 ros2 topic echo /odom --once > /dev/null 2>&1 \
            && echo 'T1.3c_odom:PASS' || echo 'T1.3c_odom:FAIL'

        # T1.3c: /cmd_vel
        timeout 8 ros2 topic info /cmd_vel > /dev/null 2>&1 \
            && echo 'T1.3c_cmd:PASS' || echo 'T1.3c_cmd:FAIL'

        kill \$LPID 2>/dev/null || true
        sleep 2
    " 2>/dev/null) || true

    for marker in T1.3a T1.3b T1.3c_scan T1.3c_odom T1.3c_cmd; do
        case $marker in
            T1.3a)       label="T1.3a  gz topics visible (/world/...)" ;;
            T1.3b)       label="T1.3b  /clock published" ;;
            T1.3c_scan)  label="T1.3c  /scan published" ;;
            T1.3c_odom)  label="T1.3c  /odom published" ;;
            T1.3c_cmd)   label="T1.3c  /cmd_vel accessible" ;;
        esac
        if echo "$launch_results" | grep -q "${marker}:PASS"; then
            _pass "$label"
        else
            _fail "$label"
        fi
    done

    # ── GUI tests (manual) ────────────────────────────────────────────────────
    if $GUI; then
        echo "  GUI tests (manual confirmation required):"
        _skip "T1.4b  Gazebo GUI shows warehouse world + TB3 robot"
        _skip "T1.4c  teleop_twist_keyboard moves robot (run: bash scripts/attach_terminal.sh turtlebot3_simulator)"
        echo
        echo "  To verify T1.4b/T1.4c:"
        echo "    1. bash scripts/attach_terminal.sh turtlebot3_simulator"
        echo "    2. ros2 launch tb3_bringup sim_bringup.launch.py"
        echo "    3. (in another terminal) ros2 launch tb3_bringup teleop.launch.py"
    fi
}

# ── Milestone 2 ───────────────────────────────────────────────────────────────
run_m2() {
    _head "Milestone 2: Gamepad Control"

    # ── Unit tests ────────────────────────────────────────────────────────────
    echo "  Unit tests (pytest):"

    run_test "T2.3u  pytest tb3_controller" \
        docker exec turtlebot3_simulator bash -c \
            "source /opt/ros/jazzy/setup.bash && cd ~/ros2_ws && \
             python3 -m pytest src/tb3_controller/test/ -q --tb=short 2>&1"

    # ── Gamepad stack (automated checks) ─────────────────────────────────────
    echo "  Gamepad stack:"

    local gp_results
    gp_results=$(docker exec turtlebot3_simulator bash -c "
        source /opt/ros/jazzy/setup.bash
        source ~/ros2_ws/install/setup.bash 2>/dev/null || true
        ros2 launch tb3_bringup gamepad.launch.py > /tmp/gp.log 2>&1 &
        GPID=\$!
        sleep 6

        # T2.2a: /joy topic has publisher (SDL2 joy_node running)
        ros2 topic info /joy 2>/dev/null | grep -q 'Publisher count: [1-9]' \
            && echo 'T2.2a:PASS' || echo 'T2.2a:FAIL'

        # T2.3a: /estop topic exists with TRANSIENT_LOCAL (initial state published)
        timeout 4 ros2 topic echo /estop --once 2>/dev/null | grep -q 'data:' \
            && echo 'T2.3a:PASS' || echo 'T2.3a:FAIL'

        # T2.3e: /cmd_vel_raw exists (teleop remapped correctly)
        ros2 topic info /cmd_vel_raw 2>/dev/null | grep -q 'Publisher count: [1-9]' \
            && echo 'T2.3e_remap:PASS' || echo 'T2.3e_remap:FAIL'

        kill \$GPID 2>/dev/null
        sleep 2
    " 2>/dev/null) || true

    for marker in T2.2a T2.3a T2.3e_remap; do
        case $marker in
            T2.2a)        label="T2.2a  /joy published (F310 detected)" ;;
            T2.3a)        label="T2.3a  /estop published (initial state latched)" ;;
            T2.3e_remap)  label="T2.3e  /cmd_vel_raw exists (teleop remapped)" ;;
        esac
        if echo "$gp_results" | grep -q "${marker}:PASS"; then
            _pass "$label"
        else
            _fail "$label"
        fi
    done

    # ── Manual tests ──────────────────────────────────────────────────────────
    if $GUI; then
        echo "  Manual tests (gamepad required):"
        _skip "T2.2b  Robot moves forward — hold RB + right stick up"
        _skip "T2.2c  Robot turns — hold RB + left stick left/right"
        _skip "T2.3a  Press B → robot stops, /estop=true, no motion"
        _skip "T2.3b  Press A → e-stop clears, motion resumes"
        _skip "T2.3c  Press Y → gamepad nodes shut down cleanly"
        echo
        echo "  To run manual M2 tests:"
        echo "    1. bash scripts/run_docker.sh (if not running)"
        echo "    2. bash scripts/attach_terminal.sh turtlebot3_simulator"
        echo "    3. ros2 launch tb3_bringup sim_bringup.launch.py"
        echo "    4. (new terminal) ros2 launch tb3_bringup gamepad.launch.py"
    fi
}

# ── Milestone 3 ───────────────────────────────────────────────────────────────
run_m3() {
    _head "Milestone 3: Autonomous Capabilities"
    _skip "M3 tests not yet implemented (Phase 3.x)"
}

# ── Main ──────────────────────────────────────────────────────────────────────
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}  TurtleBot3 Test Runner${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo "  Milestone : $MILESTONE"
echo "  GUI mode  : $GUI"

case $MILESTONE in
    m1)  run_m1 ;;
    m2)  run_m2 ;;
    m3)  run_m3 ;;
    all) run_m1; run_m2; run_m3 ;;
esac

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "  Results: ${GREEN}${TOTAL_PASS} passed${NC}  ${RED}${TOTAL_FAIL} failed${NC}  ${YELLOW}${TOTAL_SKIP} skipped${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"

[[ $TOTAL_FAIL -eq 0 ]]
