# 3DMoBot ROS2 Packages — Sync Repository

### Summary
- This repository manages and syncs the set of ROS2 packages required for the 3DMoBot project. Use it to fetch, update and prepare the source workspace for development alongised ROS2 Humble. Workflow tested on Xubuntu 22.04.

### Quick Start
- Clone the repo:
    
    ```
    mkdir src; cd src
    git clone git@github.com:Ab-Tx/3DMoBot-ros2-packages.git
    cd 3DMoBot-ros2-packages
    git submodule init
    git submodule update --recursive
    ```

- Replace RTAB-Map and Realsense launch files with the custom ones:

    ```
    mv -f replace_rtabmap_ros/* rtabmap_ros
    mv -f rs_launch.py realsense-ros/realsense2_camera/launch
    rm -r replace_rtabmap_ros
    ```
- build the workspace
    ```
    # cd to the root of your workspace first!
    export MAKEFLAGS=-j6 # Can be ignored if you have a lot of RAM (>16GB)
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
    source ./install/local_setup.bash 
    ```
- Use the [cycloneDDS](https://docs.ros.org/en/humble/Installation/RMW-Implementations/DDS-Implementations/Working-with-Eclipse-CycloneDDS.html) (recommendationf rom RTAB-Map):
    ```
    echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
    ```

### Troubleshooting

RTAB-Map and realsense-ros packages may require syncing with the latest version for compatibility with latest source of ROS2 Humble. 

### Content overview

- apriltag_ros (fork)
- my_nav2_launch 
- nav2focbox 
- opennav_docking 
- pointcloud_to_laserscan (fork)
- realsense-ros
    - ROS package for the realsense camera.
- robot_launch
    -   Launch file used to initiate near all** software used by the 3DMoBot.
- ros_odrive (fork)
    -   Odrive S1 ROS package.
- rtabmap
- rtabmap_ros
- replace_rtabmap_ros
    - Not a package. Contains several customized launch files for RTAB-Map.

** Refer to the commented information in robot.launch.py