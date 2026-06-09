FROM ros:humble-ros-base-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends iproute2 \
 && rm -rf /var/lib/apt/lists/*
 

RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        build-essential cmake python3-colcon-common-extensions \
        libpcl-dev ros-humble-pcl-conversions ros-humble-pcl-msgs ros-humble-pcl-ros \
        python3-numpy python3-dev python3-setuptools python3-pip \
    && rm -rf /var/lib/apt/lists/*


COPY --chown=root:root Livox-SDK2 /Livox-SDK2
RUN mkdir /Livox-SDK2/build && cd /Livox-SDK2/build \
 && cmake .. && make -j$(nproc) && make install \
 && echo '/usr/local/lib' > /etc/ld.so.conf.d/livox_lidar.conf && ldconfig

COPY --chown=root:root Sophus /Sophus
RUN cd /Sophus \
&& git checkout 97e7161 \
&& mkdir build && cd build \
&& cmake .. -DBUILD_TESTS=OFF \
&& make -j$(nproc) && make install \
&& echo '/usr/local/lib' > /etc/ld.so.conf.d/sophus.conf && ldconfig


# 3) Installation de GTSAM
COPY --chown=root:root gtsam /gtsam
RUN cd /gtsam \
 && git checkout 4abef92 \
 && mkdir build && cd build \
 && cmake \
      -DGTSAM_USE_SYSTEM_EIGEN=ON \
      -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
      .. \
 && make -j$(nproc) && make install \
 && echo '/usr/local/lib' > /etc/ld.so.conf.d/gtsam.conf && ldconfig

RUN apt-get update \
 && apt-get install -y \
        build-essential \
        cmake \
        cppcheck \
        gdb \
        git \
        sudo \
        vim \
        wget \
        tmux \
        curl \
        less \
        htop \
        libsm6 libxext6 libgl1-mesa-glx libxrender-dev \ 
        curl \
 && apt-get clean

RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
apt-get install -y --no-install-recommends \
    ros-humble-rviz-common \
    libceres-dev \
&& rm -rf /var/lib/apt/lists/*

RUN export DEBIAN_FRONTEND=noninteractive \
&& sudo apt-get update \
&& sudo -E apt-get install -y \
tzdata \
&& sudo ln -fs /usr/share/zoneinfo/America/Toronto/etc/localtime \
&& sudo dpkg-reconfigure --frontend noninteractive tzdata \
&& sudo apt-get clean

RUN apt-get update && apt-get install -y cmake libatlas-base-dev libeigen3-dev libpcl-dev libgoogle-glog-dev libsuitesparse-dev libglew-dev wget unzip git python3-pip
RUN apt-get install -y ros-humble-tf2 ros-humble-cv-bridge ros-humble-xacro ros-humble-robot-state-publisher \
    ros-humble-rviz2 ros-humble-image-transport ros-humble-image-transport-plugins

RUN apt-get install -y python-tk


RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
 && apt-get install -y --no-install-recommends \
       python3-pandas \
       python3-scipy \
       python3-matplotlib \
       ipython3 \
       python3-opencv \
       python3-skimage \
       python3-skimage-lib \
       python3-sklearn \
       python3-sklearn-lib \
       python3-numba \
       python3-llvmlite \
 && rm -rf /var/lib/apt/lists/*


RUN pip install numpy==1.24.3 matplotlib==3.7.1
RUN pip install --upgrade packaging
RUN pip3 install zenmav
RUN pip3 install pymavlink
RUN pip3 install geopy

RUN apt-get update && apt-get install -y --no-install-recommends \
  ros-humble-mavros \
  ros-humble-mavros-extras \
  ros-humble-mavlink \
  geographiclib-tools


RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
 && apt-get install -y --no-install-recommends \
       ros-humble-tf-transformations \
       ros-humble-pointcloud-to-laserscan \
       ros-humble-mavros-msgs \
 && rm -rf /var/lib/apt/lists/*

RUN /opt/ros/humble/lib/mavros/install_geographiclib_datasets.sh

RUN pip install --no-cache-dir --upgrade transforms3d


RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
 && apt-get install -y --no-install-recommends \
        libvtk9-dev \
        ros-humble-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ENV PROJECT_DIR=/ros2_ws/src           \
    DATASET_DIR=/data

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

WORKDIR /ros2_ws