

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import LoadComposableNodes
from launch_ros.actions import Node
from launch_ros.descriptions import ComposableNode, ParameterFile
from nav2_common.launch import RewrittenYaml


from launch import LaunchDescription
from launch_ros.actions import Node, SetParameter
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():


    return LaunchDescription([        # launch collision monitor
        
        # # SLAM
        IncludeLaunchDescription(
            PathJoinSubstitution([ PathJoinSubstitution([FindPackageShare('rtabmap_launch'), 'launch']), 'interbot+rsdepth.launch.py'])
        ),
        # URDF is in package 'sam_bot_description', it is published by ~~the SLAM algorithm's launch file~~ the odrive botwheel_explorer launch file 
        # (using pkg: robot_state_publisher, joint_state_publisher)

        # Nav2
        IncludeLaunchDescription(
            PathJoinSubstitution([ PathJoinSubstitution([FindPackageShare('my_nav2_launch'), 'launch']), 'navigation_dock_launch.py']),
            launch_arguments={'params_file': '/home/xu22pc/dev/rtabmap_ws2/src/my_nav2_launch/params/nav2_params.yaml', 'use_sim_time': 'false','log_level': 'warn'}.items()
        ), # params_file:=/home/xu22pc/dev/rtabmap_ws2/src/my_nav2_launch/params/nav2_params.yaml
        IncludeLaunchDescription(
            PathJoinSubstitution([ PathJoinSubstitution([FindPackageShare('my_nav2_launch'), 'launch']), 'collision_monitor_node.launch.py']),
            launch_arguments={'params_file': '/home/xu22pc/dev/rtabmap_ws2/src/my_nav2_launch/params/collision_monitor_params_realsense.yaml', 'use_sim_time': 'false'}.items()
        ), # params_file:=/home/xu22pc/dev/colcon_ws/src/my_nav2_launch/params/collision_monitor_params.yaml 
        IncludeLaunchDescription(
            PathJoinSubstitution([ PathJoinSubstitution([FindPackageShare('pointcloud_to_laserscan'), 'launch']), 'sample_pointcloud_to_laserscan_launch.py'])
        ), 
        IncludeLaunchDescription(
            PathJoinSubstitution([ PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch']), 'rviz_launch.py']),
            launch_arguments={'headless': 'false'}.items()
        ), # headless:=false
        IncludeLaunchDescription(
            PathJoinSubstitution([ PathJoinSubstitution([FindPackageShare('odrive_botwheel_explorer'), 'launch']), 'botwheel_explorer.launch.py']),
            launch_arguments={'headless': 'false'}.items()
        ), # headless:=false

        Node( # for focbox unity board only
            package='nav2focbox', executable='process_cmd_vel2', output='screen',
        ),


        # Node( # for focbox unity board only
        #     package='nav2focbox', executable='process_cmd_vel', output='screen',
        # ),
        # -> Start ros1 docker seperately with the focbox unity ros driver
        # -> Start ouster ros driver sperately (absent here on purpose)
        # -> Start ros1_bridge seperately (absent here on purpose)
        
        # Node(
        #     package='pointcloud_to_laserscan', executable='sample_pointcloud_to_laserscan_launch.py', output='screen',
        # ),

    ])
