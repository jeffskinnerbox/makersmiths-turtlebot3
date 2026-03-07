#!/usr/bin/env bash
# run_tests.sh — Phase 8 test orchestrator
#
# Manages the container lifecycle for each test stage: docker restart → start
# the appropriate ROS 2 stack → run pytest → copy JUnit XML results to host.
#
# Usage (from repo root):
#   bash scripts/run_tests.sh [sim|obstacle|slam|nav2|all] [--gui]
#
# Options:
#   --gui   Launch Gazebo with its GUI client visible on the host display.
#           Requires: xhost +local:docker (run once per login on the host).
#           Without --gui, all stages run headless (default; safe for CI).
#
# Stages:
#   sim      — sim_bringup headless → T1, T2, T3, T4
#   obstacle — sim_bringup + obstacle_avoidance → T5
#   slam     — slam.launch headless → T6
#   nav2     — nav2_bringup headless → T7
#   all      — run all stages in order (docker restart between each)
#
# Results written to: ./test-results/results_<stage>.xml
#
# Requirements:
#   - Containers already built: bash scripts/build.sh
#   - Containers running:       sg docker -c "docker compose up -d"
#   - Run from repo root (where docker-compose.yml lives)

set -euo pipefail

CONTAINER="turtlebot3_simulator"
RESULTS_DIR="${PWD}/test-results"
TEST_DIR="src/tb3_bringup/test"

# Parse args: positional = stage, --gui = show Gazebo GUI
STAGE="all"
GUI=false
for arg in "$@"; do
    case "$arg" in
        --gui) GUI=true ;;
        *)     STAGE="$arg" ;;
    esac
done

# headless:=false → gz sim client (GUI) is launched; requires xhost +local:docker
HEADLESS_ARG="headless:=true"
if [[ "$GUI" == "true" ]]; then
    HEADLESS_ARG="headless:=false"
    echo "==> GUI mode: Gazebo client will open on host display (DISPLAY=${DISPLAY:-unset})"
    echo "==> Ensure you have run: xhost +local:docker"
fi

mkdir -p "$RESULTS_DIR"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log() { echo "==> $*"; }

ros_exec() {
    # Run a command inside the container with both setups sourced
    docker exec "$CONTAINER" bash -c "
        source /opt/ros/jazzy/setup.bash &&
        source ~/ros2_ws/install/setup.bash &&
        $*"
}

restart_container() {
    log "Restarting $CONTAINER (clean state)..."
    docker restart "$CONTAINER"
    # Wait for entrypoint to finish and ROS to be usable
    sleep 8
    docker exec "$CONTAINER" bash -c "source /opt/ros/jazzy/setup.bash && ros2 --help" \
        > /dev/null 2>&1
    log "Container ready."
}

start_bg() {
    # Start a launch file in the background inside the container
    local launch_cmd="$1"
    local wait_s="${2:-20}"
    log "Launching (bg): $launch_cmd"
    docker exec -d "$CONTAINER" bash -c "
        source /opt/ros/jazzy/setup.bash &&
        source ~/ros2_ws/install/setup.bash &&
        $launch_cmd"
    log "Waiting ${wait_s}s for stack to initialize..."
    sleep "$wait_s"
}

run_pytest() {
    local label="$1"
    shift
    local xml_container="/tmp/results_${label}.xml"
    log "Running pytest stage: $label"
    # Run pytest inside container; capture exit code without aborting the script
    ros_exec "cd ~/ros2_ws && python3 -m pytest $* -v --tb=short \
        --junit-xml=${xml_container}" || true
    docker cp "${CONTAINER}:${xml_container}" "${RESULTS_DIR}/results_${label}.xml" \
        2>/dev/null || log "WARNING: could not copy ${xml_container} from container"
    log "Results saved: ${RESULTS_DIR}/results_${label}.xml"
}

# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

stage_sim() {
    restart_container
    start_bg "ros2 launch tb3_bringup sim_bringup.launch.py $HEADLESS_ARG" 20
    run_pytest "sim" \
        "$TEST_DIR/test_t1_container_startup.py" \
        "$TEST_DIR/test_t2_topic_comms.py" \
        "$TEST_DIR/test_t3_gazebo_launch.py" \
        "$TEST_DIR/test_t4_drive_command.py"
}

stage_obstacle() {
    restart_container
    start_bg "ros2 launch tb3_bringup sim_bringup.launch.py $HEADLESS_ARG" 20
    start_bg "ros2 launch tb3_bringup obstacle_avoidance.launch.py" 5
    run_pytest "obstacle" "$TEST_DIR/test_t5_obstacle_avoidance.py"
}

stage_slam() {
    restart_container
    start_bg "ros2 launch tb3_bringup slam.launch.py $HEADLESS_ARG" 30
    run_pytest "slam" "$TEST_DIR/test_t6_slam.py"
}

stage_nav2() {
    restart_container
    # nav2_bringup delays Nav2 by 15 s internally; allow extra wall-clock time
    start_bg "ros2 launch tb3_bringup nav2_bringup.launch.py $HEADLESS_ARG" 35
    run_pytest "nav2" "$TEST_DIR/test_t7_nav2.py"
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

case "$STAGE" in
    sim)      stage_sim ;;
    obstacle) stage_obstacle ;;
    slam)     stage_slam ;;
    nav2)     stage_nav2 ;;
    all)
        stage_sim
        stage_obstacle
        stage_slam
        stage_nav2
        ;;
    *)
        echo "Usage: $0 [sim|obstacle|slam|nav2|all]"
        exit 1
        ;;
esac

log "Done. Results in ${RESULTS_DIR}/"
ls -lh "${RESULTS_DIR}/"
