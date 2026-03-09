#!/usr/bin/env bash
# tmux_dashboard.sh — TurtleBot3 monitoring dashboard
# Creates (or reattaches to) a tmux session 'tb3_monitor' inside the simulator container.
# Usage: bash scripts/tmux_dashboard.sh [--no-attach]
#
# Layout:
#   ┌────────────────────┬────────────────────┐
#   │  ros2 node list    │  /cmd_vel          │
#   ├────────────────────┼────────────────────┤
#   │  /closest_obstacle │  /odom position    │
#   ├────────────────────┴────────────────────┤
#   │  /rosout  (node logs)                   │
#   └─────────────────────────────────────────┘
#
# G3: designed for interactive use by the user.
# --no-attach: create session without attaching (used by run_tests.sh).
set -euo pipefail

CONTAINER="turtlebot3_simulator"
SESSION="tb3_monitor"
ATTACH=true
SRC="source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash 2>/dev/null || true"

# ── Argument parsing ──────────────────────────────────────────────────────────
for arg in "$@"; do
    case $arg in
        --no-attach) ATTACH=false ;;
        -h|--help)
            sed -n '2,8p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
die() { echo "ERROR: $*" >&2; exit 1; }
t_exec() { docker exec "$CONTAINER" tmux "$@"; }
t_keys() { local pane="$1"; shift; t_exec send-keys -t "${SESSION}:0.${pane}" "$*" Enter; }

# ── Container check ───────────────────────────────────────────────────────────
docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null \
    | grep -q '^true$' \
    || die "Container '$CONTAINER' is not running. Start it with: sg docker -c \"bash scripts/run_docker.sh\""

# ── Idempotency: attach if session already alive ──────────────────────────────
if t_exec has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists — attaching."
    if $ATTACH; then
        docker exec -it "$CONTAINER" tmux attach-session -t "$SESSION"
    fi
    exit 0
fi

# ── Build the 5-pane layout ───────────────────────────────────────────────────
# Pane numbering after splits:
#   0 = row1-left  (node list)          created by new-session
#   1 = bottom     (/rosout)            split-window -v -l 8 from p0
#   2 = row1-right (/cmd_vel)           split-window -h from p0
#   3 = row2-left  (/closest_obstacle)  split-window -v from p0
#   4 = row2-right (/odom position)     split-window -v from p2
t_exec new-session  -d -s "$SESSION" -x 220 -y 50
t_exec split-window -t "${SESSION}:0.0" -v -l 8   # p1: bottom strip
t_exec select-pane  -t "${SESSION}:0.0"
t_exec split-window -t "${SESSION}:0.0" -h         # p2: right column
t_exec split-window -t "${SESSION}:0.0" -v         # p3: row2-left
t_exec split-window -t "${SESSION}:0.2" -v         # p4: row2-right

# Pane border titles (tmux ≥ 2.6)
t_exec set-option  -t "$SESSION" pane-border-status top
t_exec select-pane -t "${SESSION}:0.0" -T "Nodes"
t_exec select-pane -t "${SESSION}:0.1" -T "/rosout"
t_exec select-pane -t "${SESSION}:0.2" -T "/cmd_vel"
t_exec select-pane -t "${SESSION}:0.3" -T "/closest_obstacle"
t_exec select-pane -t "${SESSION}:0.4" -T "/odom"

# ── Send commands to each pane ────────────────────────────────────────────────
t_keys 0 "$SRC && watch -n 3 'ros2 node list 2>/dev/null || echo \"(waiting for nodes…)\"'"
t_keys 2 "$SRC && ros2 topic echo /cmd_vel"
t_keys 3 "$SRC && ros2 topic echo /closest_obstacle"
t_keys 4 "$SRC && ros2 topic echo /odom --field pose.pose.position"
t_keys 1 "$SRC && ros2 topic echo /rosout"

t_exec select-pane -t "${SESSION}:0.0"
echo "Dashboard '${SESSION}' ready (5 panes)."

# ── Attach ────────────────────────────────────────────────────────────────────
if $ATTACH; then
    docker exec -it "$CONTAINER" tmux attach-session -t "$SESSION"
fi
