# HML-LiDAR RevA processing environment
# Field-tested reference environment:
#   Ubuntu 22.04 / ROS 2 Humble / Python 3.10
#
# Source dependencies are pinned to the exact Git commits used for RevA.
# System packages are installed from the Ubuntu 22.04 / ROS 2 Humble repositories.
#
# IMPORTANT:
# The field-processing container used for RevA was amd64.
# The target platform will be fixed to linux/amd64 in docker-compose.yml.

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_DISTRO=humble
ENV HML_WS=/opt/hml_ws

# ---------------------------------------------------------------------------
# Exact source revisions used for HML-LiDAR RevA
# ---------------------------------------------------------------------------
ARG DLIO_COMMIT=c8acc37100e349d70a9d8432d656cbce7e5072cd
ARG LIVOX_DRIVER_COMMIT=6b9356cadf77084619ba406e6a0eb41163b08039
ARG LIVOX_SDK2_COMMIT=6a940156dd7151c3ab6a52442d86bc83613bd11b

# ---------------------------------------------------------------------------
# Base system, compiler toolchain, and ROS 2 repository
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg2 \
    locales \
    lsb-release \
    software-properties-common \
    git \
    build-essential \
    cmake \
    libeigen3-dev \
    libomp-dev \
    libpcl-dev \
    libapr1-dev \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && add-apt-repository universe -y \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
      > /etc/apt/sources.list.d/ros2.list

# ---------------------------------------------------------------------------
# ROS 2 Humble packages required by DLIO, Livox, rosbag processing and Foxglove
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ros-base \
    ros-humble-rosbridge-server \
    ros-humble-pcl-ros \
    ros-humble-pcl-conversions \
    ros-humble-ament-cmake-auto \
    ros-humble-rosidl-default-generators \
    ros-humble-rosidl-default-runtime \
    ros-humble-rosbag2 \
    ros-humble-rosbag2-py \
    ros-humble-rosbag2-storage-default-plugins \
    ros-humble-sensor-msgs-py \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Python versions observed in the field-processing RevA container
# ---------------------------------------------------------------------------
RUN python3 -m pip install --no-cache-dir \
    numpy==1.21.5 \
    scipy==1.8.0 \
    rosbags==0.11.1

# ---------------------------------------------------------------------------
# Livox-SDK2 — exact RevA source revision
# ---------------------------------------------------------------------------
RUN git clone https://github.com/Livox-SDK/Livox-SDK2.git /opt/Livox-SDK2 \
    && cd /opt/Livox-SDK2 \
    && git checkout "${LIVOX_SDK2_COMMIT}" \
    && mkdir -p build \
    && cd build \
    && cmake .. \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig

# ---------------------------------------------------------------------------
# ROS 2 workspace: Livox ROS Driver 2 + DLIO
# ---------------------------------------------------------------------------
RUN mkdir -p "${HML_WS}/src"

# Livox ROS Driver 2 — exact RevA source revision
RUN git clone https://github.com/Livox-SDK/livox_ros_driver2.git \
      "${HML_WS}/src/livox_ros_driver2" \
    && cd "${HML_WS}/src/livox_ros_driver2" \
    && git checkout "${LIVOX_DRIVER_COMMIT}" \
    && cp -f package_ROS2.xml package.xml \
    && rm -rf launch \
    && cp -rf launch_ROS2 launch

RUN /bin/bash -lc \
    "source /opt/ros/humble/setup.bash && \
     cd ${HML_WS} && \
     colcon build \
       --packages-select livox_ros_driver2 \
       --cmake-args \
         -DROS_EDITION=ROS2 \
         -DHUMBLE_ROS=humble \
         -DCMAKE_BUILD_TYPE=Release"

# DLIO — exact RevA source revision
RUN git clone https://github.com/vectr-ucla/direct_lidar_inertial_odometry.git \
      "${HML_WS}/src/direct_lidar_inertial_odometry" \
    && cd "${HML_WS}/src/direct_lidar_inertial_odometry" \
    && git checkout "${DLIO_COMMIT}"

RUN /bin/bash -lc \
    "source /opt/ros/humble/setup.bash && \
     source ${HML_WS}/install/setup.bash && \
     cd ${HML_WS} && \
     colcon build \
       --symlink-install \
       --packages-select direct_lidar_inertial_odometry \
       --cmake-args -DCMAKE_BUILD_TYPE=Release"

# ---------------------------------------------------------------------------
# Runtime environment
# ---------------------------------------------------------------------------
RUN printf '%s\n' \
    'source /opt/ros/humble/setup.bash' \
    'source /opt/hml_ws/install/setup.bash' \
    >> /root/.bashrc

# User data/workspace is intentionally separate from /opt/hml_ws so that
# volume mounts cannot hide the compiled RevA software stack.
RUN mkdir -p /root/data /root/ros2_ws/results

WORKDIR /root/ros2_ws

CMD ["bash"]
