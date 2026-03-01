---
name: ros2-jazzy-workspace
description: Design, scaffold, and manage a ROS 2 Jazzy Jalisco workspace (ros2_ws). Use this skill when the user asks how to structure a ROS 2 workspace, organize packages into layers or groups, set up a multi-repo workspace with vcstool, configure rosdep, manage colcon build options and overlays, establish workspace conventions (naming, versioning, branching), create a workspace-level Makefile or justfile, or plan a monorepo vs multi-repo strategy. This is a workspace design and tooling skill — it produces directory layouts, configuration files, build scripts, and structured conventions.
---

This skill guides the design and management of ROS 2 Jazzy Jalisco workspaces. A well-designed workspace is the foundation of a productive ROS 2 project: it determines how fast you build, how easy it is to onboard contributors, how cleanly you can deploy, and whether your CI pipeline is maintainable. Poor workspace structure causes cascading problems — broken overlays, mysterious build failures, and unresolvable dependency cycles.

---

## 1. Workspace Anatomy

A ROS 2 workspace has a strict internal structure created by `colcon`. Understanding it prevents the most common workspace mistakes.

```
ros2_ws/                          ← Workspace root (never build here)
├── src/                          ← ALL source packages live here
│   ├── my_robot_bringup/
│   ├── my_robot_description/
│   ├── my_robot_navigation/
│   └── my_robot_drivers/
│
├── build/                        ← colcon build artifacts (auto-generated, gitignored)
│   └── <package_name>/
│
├── install/                      ← Installed packages & setup scripts (auto-generated, gitignored)
│   ├── setup.bash                ← SOURCE THIS to use the workspace
│   ├── setup.zsh
│   └── local_setup.bash          ← Only this workspace, not underlays
│
├── log/                          ← colcon and test logs (auto-generated, gitignored)
│
├── .repos                        ← vcstool multi-repo manifest (committed to git)
├── .colcon/                      ← Workspace-level colcon defaults
│   └── defaults.yaml
├── Makefile                      ← Convenience build/run shortcuts (optional)
└── README.md
```

### The Golden Rule

**Always source before you use.** The sequence is always:

```bash
source /opt/ros/jazzy/setup.bash       # 1. Underlay (system ROS install)
cd ~/ros2_ws
colcon build                           # 2. Build
source install/setup.bash              # 3. Overlay (your workspace)
```

Never `source install/setup.bash` before building — it creates a stale overlay that can silently shadow your newly built packages.

---

## 2. Package Layering Strategy

Structure packages into logical layers. This enforces a clean dependency graph and prevents circular dependencies.

### The Four-Layer Model

```
┌─────────────────────────────────────────────────────┐
│  LAYER 4 — BRINGUP                                  │
│  (launch files, top-level configs, integration)     │
│  my_robot_bringup                                   │
├─────────────────────────────────────────────────────┤
│  LAYER 3 — APPLICATIONS                             │
│  (navigation, manipulation, perception pipelines)   │
│  my_robot_navigation   my_robot_perception          │
├─────────────────────────────────────────────────────┤
│  LAYER 2 — CORE / BUSINESS LOGIC                    │
│  (algorithms, state machines, controllers)          │
│  my_robot_control   my_robot_planning               │
├─────────────────────────────────────────────────────┤
│  LAYER 1 — INTERFACES & MESSAGES                    │
│  (custom msgs, srvs, actions — no node code here)   │
│  my_robot_msgs   my_robot_interfaces                │
├─────────────────────────────────────────────────────┤
│  LAYER 0 — HARDWARE ABSTRACTION                     │
│  (drivers, sensor nodes, hardware-facing only)      │
│  my_robot_drivers   my_robot_hardware_interface     │
└─────────────────────────────────────────────────────┘
    Dependencies flow strictly UPWARD only.
    Layer N may only depend on Layer N-1 and below.
```

### Dependency Direction Rule

**A package may ONLY depend on packages in the same or lower layer.** If your navigation package needs to import from your bringup package, that is a design error — refactor the shared logic into a lower layer.

---

## 3. Package Naming Conventions

Consistent naming makes `colcon build --packages-select` and `rosdep` commands predictable and self-documenting.

### Convention: `<robot_name>_<layer_or_function>`

| Pattern | Example | Layer |
|---|---|---|
| `<robot>_msgs` | `bumper_bot_msgs` | Interfaces (Layer 1) |
| `<robot>_description` | `bumper_bot_description` | Hardware (URDF, meshes) |
| `<robot>_drivers` | `bumper_bot_drivers` | Hardware (Layer 0) |
| `<robot>_hardware_interface` | `bumper_bot_hardware_interface` | ros2_control HAL |
| `<robot>_control` | `bumper_bot_control` | Core (Layer 2) |
| `<robot>_navigation` | `bumper_bot_navigation` | Applications (Layer 3) |
| `<robot>_perception` | `bumper_bot_perception` | Applications (Layer 3) |
| `<robot>_bringup` | `bumper_bot_bringup` | Bringup (Layer 4) |
| `<robot>_sim` | `bumper_bot_sim` | Simulation (parallel to bringup) |
| `<robot>_tests` | `bumper_bot_tests` | Integration test package |

### What Goes Where

| Item | Package |
|---|---|
| Custom `.msg`, `.srv`, `.action` files | `<robot>_msgs` or `<robot>_interfaces` |
| URDF / xacro files | `<robot>_description` |
| Mesh files (`.stl`, `.dae`) | `<robot>_description/meshes/` |
| Top-level launch files | `<robot>_bringup/launch/` |
| Shared parameter files | `<robot>_bringup/config/` |
| Simulation world files | `<robot>_sim/worlds/` |
| RViz config files | `<robot>_bringup/rviz/` |

---

## 4. `src/` Directory Organization

For a single robot:

```
src/
├── bumper_bot_msgs/
├── bumper_bot_description/
├── bumper_bot_drivers/
├── bumper_bot_hardware_interface/
├── bumper_bot_control/
├── bumper_bot_perception/
├── bumper_bot_navigation/
├── bumper_bot_sim/
└── bumper_bot_bringup/
```

For a multi-robot or product-line workspace, group packages by robot or product:

```
src/
├── common/                          ← Shared packages (used by all robots)
│   ├── common_msgs/
│   └── common_sensors/
├── bumper_bot/                      ← Robot A packages
│   ├── bumper_bot_msgs/
│   └── bumper_bot_bringup/
└── scout_bot/                       ← Robot B packages
    ├── scout_bot_msgs/
    └── scout_bot_bringup/
```

---

## 5. `.repos` File — Multi-Repo Workspace Management

For workspaces that span multiple git repositories, use `vcstool` with a `.repos` manifest. This is the standard pattern for production ROS 2 projects.

### `.repos` file format

```yaml
# ros2_ws/.repos
repositories:
  bumper_bot_bringup:
    type: git
    url: https://github.com/myorg/bumper_bot_bringup.git
    version: main

  bumper_bot_navigation:
    type: git
    url: https://github.com/myorg/bumper_bot_navigation.git
    version: jazzy-devel

  nav2:
    type: git
    url: https://github.com/ros-navigation/navigation2.git
    version: jazzy

  slam_toolbox:
    type: git
    url: https://github.com/SteveMacenski/slam_toolbox.git
    version: ros2
```

### vcstool Commands

```bash
# Install vcstool
pip install vcstool --break-system-packages
# OR
sudo apt install python3-vcstool

# Clone all repositories listed in .repos into src/
vcs import src < .repos

# Update all repos to their declared version
vcs pull src

# Export current state of all repos (generates a new .repos snapshot)
vcs export src > .repos.snapshot

# Check status of all repos at once
vcs status src
```

---

## 6. `rosdep` — Dependency Management

`rosdep` resolves ROS and system package dependencies declared in `package.xml`. Always run it after cloning new packages.

```bash
# Initialize rosdep (once per machine)
sudo rosdep init
rosdep update

# Install all dependencies for every package in src/
rosdep install --from-paths src --ignore-src -r -y

# Install deps for specific packages only
rosdep install --from-paths src/bumper_bot_navigation --ignore-src -y

# Check what would be installed without installing
rosdep check --from-paths src --ignore-src

# Install for a specific OS/version (useful in CI)
rosdep install --from-paths src --ignore-src -r -y \
  --os=ubuntu:noble --rosdistro=jazzy
```

---

## 7. colcon Build Configuration

### Workspace-Level Defaults (`~/.colcon/defaults.yaml` or `ros2_ws/.colcon/defaults.yaml`)

```yaml
# .colcon/defaults.yaml
build:
  symlink-install: true          # Python: no rebuild after source edits
  cmake-args:
    - "-DCMAKE_BUILD_TYPE=RelWithDebInfo"
    - "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"   # Enables clangd / IDE integration
  event-handlers:
    - console_cohesion+           # Groups output per package (cleaner logs)

test:
  event-handlers:
    - console_direct+
```

### Key `colcon build` Flags

```bash
# Full workspace build
colcon build

# Build only changed packages and their dependents
colcon build --packages-up-to my_package

# Build a specific package and all its dependencies
colcon build --packages-up-to bumper_bot_bringup

# Build only a specific package (no dependencies rebuilt)
colcon build --packages-select bumper_bot_msgs

# Build multiple specific packages
colcon build --packages-select bumper_bot_msgs bumper_bot_drivers

# Skip packages that fail (useful when working on one package)
colcon build --continue-on-error

# Parallel jobs (default is num_cpus, reduce to avoid OOM on large builds)
colcon build --parallel-workers 4

# Full clean rebuild
rm -rf build/ install/ log/
colcon build
```

### Colcon Package Ignore

To exclude a package from all colcon operations, place a `COLCON_IGNORE` file in its directory:

```bash
touch src/experimental_package/COLCON_IGNORE
```

---

## 8. Workspace Overlays

Overlays allow you to layer workspaces — your workspace builds on top of the system ROS install, and additional workspaces can build on top of yours.

### Overlay Chain

```
/opt/ros/jazzy/setup.bash          ← Underlay: system Jazzy install (always first)
    ↓
~/ros2_ws/install/setup.bash       ← Your workspace overlay
    ↓
~/ros2_ws_experimental/install/setup.bash   ← Development overlay on top (optional)
```

### Rules for Overlays

- **Source underlays before building** the overlay — otherwise the overlay won't find its dependencies.
- **`setup.bash` vs `local_setup.bash`**: `setup.bash` sources the full chain (underlay + this workspace). `local_setup.bash` sources only this workspace. Use `local_setup.bash` when you have already sourced the underlay.
- **Never build inside a container with a sourced overlay from a previous run** — always `source` after each build.
- **Keep your overlay workspace small.** Only put packages you are actively developing in your overlay workspace. Use `--packages-select` aggressively.

---

## 9. Workspace Makefile (Convenience Wrapper)

A workspace-level `Makefile` or `justfile` dramatically reduces the cognitive load of daily operations.

### `Makefile`

```makefile
# ros2_ws/Makefile
.PHONY: build build-clean test lint source setup deps

SHELL := /bin/bash
COLCON_FLAGS ?= --symlink-install

## Build the workspace
build:
 source /opt/ros/jazzy/setup.bash && \
 colcon build $(COLCON_FLAGS)

## Clean build artifacts and rebuild
build-clean:
 rm -rf build/ install/ log/
 source /opt/ros/jazzy/setup.bash && \
 colcon build $(COLCON_FLAGS)

## Install all rosdep dependencies
deps:
 source /opt/ros/jazzy/setup.bash && \
 rosdep install --from-paths src --ignore-src -r -y

## Run all tests
test:
 source /opt/ros/jazzy/setup.bash && \
 source install/setup.bash && \
 colcon test && \
 colcon test-result --verbose

## Run linting only
lint:
 source /opt/ros/jazzy/setup.bash && \
 colcon test --packages-select $$(colcon list --names-only) \
   --pytest-args -k "flake8 or pep257 or copyright"

## Clone / update all repos from .repos file
setup:
 vcs import src < .repos
 $(MAKE) deps
 $(MAKE) build

## Show workspace package list with dependencies
info:
 source /opt/ros/jazzy/setup.bash && \
 colcon list --topological-order

## Print how to source the workspace
source:
 @echo "Run: source install/setup.bash"
```

---

## 10. `.gitignore` for a ROS 2 Workspace

```gitignore
# ROS 2 workspace generated directories
build/
install/
log/

# colcon generated
.colcon_install_layout

# Python cache
__pycache__/
*.py[cod]
*.egg-info/

# CMake
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
Makefile
compile_commands.json

# IDE
.vscode/settings.json
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## 11. Monorepo vs. Multi-Repo Strategy

### Monorepo (all packages in one git repository)

**Best for:** Small teams, single robot, rapid prototyping, academic projects.

```
my_robot/                   ← Single git repository
├── .devcontainer/
├── .github/
├── src/
│   ├── my_robot_msgs/
│   ├── my_robot_drivers/
│   └── my_robot_bringup/
├── .repos                  ← Points to external dependencies only
└── Makefile
```

**Pros:** Simple CI, atomic commits across packages, easy to search, no version coordination overhead.
**Cons:** Large repository over time, all-or-nothing access control, can't reuse packages across robots easily.

### Multi-Repo (each package or package group in its own repository)

**Best for:** Multiple robots sharing packages, larger teams with ownership separation, open-source components.

```
# Each lives in its own git repository:
github.com/myorg/robot_msgs
github.com/myorg/robot_drivers
github.com/myorg/robot_bringup

# The workspace repository contains only:
my_robot_ws/
├── .repos          ← Declares all the above repos + versions
└── Makefile
```

**Pros:** Independent versioning, clear ownership, selective access control, reusable packages.
**Cons:** Version coordination complexity, requires vcstool discipline, harder atomic cross-package changes.

### Recommended Decision Matrix

| Factor | Monorepo | Multi-Repo |
|---|---|---|
| Team size | 1–5 developers | 5+ developers |
| Number of robots | 1 | 2+ |
| Package reuse | Low | High |
| CI complexity tolerance | Low | Medium–High |
| Open-source components | No | Yes |

---

## 12. Workspace Designer Gotchas

- **Never `colcon build` from inside `src/`** — always from the workspace root (`ros2_ws/`). Building from `src/` creates `build/`, `install/`, `log/` inside your source tree and corrupts the workspace.
- **The `install/` directory is not a deployment artifact** — it's a development overlay. For deployment, build a Debian package (`bloom-release`) or Docker image instead.
- **`--symlink-install` breaks on Windows** and inside some Docker volume configurations. If builds seem stale despite changes, disable it and do a clean build.
- **Circular dependencies between packages cause `colcon` to error** with a cryptic topological sort failure. Run `colcon graph` to visualize the dependency graph and find cycles.
- **Package names must be unique across the entire workspace** including all underlay packages. If you name your package `rclpy` or `std_msgs` you will shadow the system package and break everything.
- **`rosdep` and custom packages**: `rosdep` will only find packages in its database. For your own packages that other packages depend on, use `--ignore-src` so `rosdep` skips them (they are already in `src/`).
- **Version pinning in `.repos`**: Always pin to a specific tag or commit SHA in production. Pointing to `main` means `vcs import` will pull different code over time, breaking reproducibility.
- **Build order matters for message packages**: Always build `<robot>_msgs` first. If `colcon build` fails because a message type is not found, build just the messages package first: `colcon build --packages-select my_robot_msgs`.
- **`local_setup.bash` in CI**: In CI pipelines, source `local_setup.bash` (not `setup.bash`) after the underlay is already sourced to avoid double-sourcing warnings that can confuse log parsers.
