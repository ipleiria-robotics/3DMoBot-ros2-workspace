
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.actions import SetParameter

import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    odom_parameters=[{
        'frame_id':'kinect',
        # ground truth here is just used to align odometry with ground truth's first pose
        # 'ground_truth_frame_id':'world',
        # 'ground_truth_base_frame_id':'kinect_gt',
        'keep_color': True,
        'wait_for_transform': 0.5,
        # RTAB-Map's parameters should all be string type:
        'Odom/Strategy':'0',
        'Odom/ResetCountdown':'15',
        'Odom/GuessSmoothingDelay':'0',
    }]
    slam_parameters=[{
          'frame_id':'kinect',
          # Record ground truth to compute RMSE
          # 'ground_truth_frame_id':'world',
          # 'ground_truth_base_frame_id':'kinect_gt',
          'subscribe_rgb':False,
          'subscribe_depth':False,
          'subscribe_rgbd':True,
          'subscribe_odom_info':True,
          # RTAB-Map's parameters should all be string type:
          'Mem/UseOdomFeatures': 'true',
          'Rtabmap/StartNewMapOnLoopClosure':'true',
          'RGBD/CreateOccupancyGrid':'false',
          'Rtabmap/CreateIntermediateNodes':'true',
          'RGBD/LinearUpdate':'0',
          'RGBD/AngularUpdate':'0'}]
          
    odom_remappings=[
          ('rgb/image', '/camera/color/image_raw'),
          ('rgb/camera_info', '/camera/color/camera_info'),
          ('depth/image', '/camera/depth/image_rect_raw')]
    
    # We will use the output of odometry to avoid re-extracting 
    # the same features on slam side.
    slam_remappings=[
        ("rgbd_image", "odom_rgbd_image")]
          

    return LaunchDescription([

        SetParameter(name='use_sim_time', value=False),
        # 'use_sim_time' will be set on all nodes following the line above

        # Launch arguments
        DeclareLaunchArgument(
            'unite_imu_method', default_value='2',
            description='0-None, 1-copy, 2-linear_interpolation. Use unite_imu_method:="1" if imu topics stop being published.'),

        # Launch camera driver
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('realsense2_camera'), 'launch'),
                '/rs_launch.py']),
                launch_arguments={'camera_namespace': '',
                                'enable_gyro': 'true',
                                'enable_accel': 'true',
                                'unite_imu_method': LaunchConfiguration('unite_imu_method'),
                                'enable_depth': 'true',
                                'enable_infra': 'true',
                                'enable_infra1': 'true',
                                'enable_infra2': 'true',
                                'enable_sync': 'true',
                                # 'enable_rgbd': 'true',
                                'align_depth.enable': 'true'}.items(),
        ),

        # Nodes to launch
        Node(
            package='rtabmap_odom', executable='rgbd_odometry', output='screen',
            parameters=odom_parameters,
            remappings=odom_remappings),

        Node(
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=slam_parameters,
            remappings=slam_remappings,
            arguments=['-d']),

        Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=slam_parameters,
            remappings=slam_remappings),
   ])
