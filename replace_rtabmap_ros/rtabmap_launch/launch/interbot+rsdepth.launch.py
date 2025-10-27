# Example:
#
#   Bringup turtlebot3:
#     $ export TURTLEBOT3_MODEL=waffle
#     $ export LDS_MODEL=LDS-01
#     $ ros2 launch turtlebot3_bringup robot.launch.py
#
#   SLAM:
#     $ ros2 launch rtabmap_demos turtlebot3_rgbd.launch.py
#
#   Navigation (install nav2_bringup package):
#     $ ros2 launch nav2_bringup navigation_launch.py
#     $ ros2 launch nav2_bringup rviz_launch.py
#
#   Teleop:
#     $ ros2 run turtlebot3_teleop teleop_keyboard
# ---
# Requirements:
#   A realsense D435i
#   Install realsense2 ros2 package (ros-$ROS_DISTRO-realsense2-camera)
# Example:
#   $ ros2 launch rtabmap_examples realsense_d435i_infra.launch.py

import os

from ament_index_python.packages import get_package_share_directory

# debug ---
import launch_ros.actions
from launch.substitutions import TextSubstitution
# debug ---

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
    use_sim_time = LaunchConfiguration('use_sim_time')
    localization = LaunchConfiguration('localization')

    parameters=[
        {
          'frame_id': 'base_link',
          'subscribe_depth':True,
        #   'subscribe_rgb': False, # use default
          'subscribe_stereo':False,
        #   'publish_tf_odom':'true',    # new
          'odom_frame_id':'odom',
        #   'odom_tf_linear_variance':'0.001',    # new
        #   'odom_tf_angular_variance':'0.001',   # new
          'subscribe_odom_info':True,
          'use_sim_time':use_sim_time,
          'approx_sync':False,
          'use_action_for_goal':True,
          'Reg/Force3DoF':'true',
          'Grid/RayTracing':'true', # Fill empty space
          'Grid/3D':'true', # Use 2D occupancy
          'Grid/FromDepth':'true',
          'Grid/CellSize':'0.05',
          'Grid/RangeMax':'10.0',
          'Grid/OccupancyThr':'0.6', # default: 0.5 @todo test
          'Grid/NormalsSegmentation':'true', # Use passthrough filter to detect obstacles
          'Grid/MaxGroundHeight':'0.05', # All points above 5 cm are obstacles
          'Grid/MaxObstacleHeight':'0.4',  # All points over 1 meter are ignored
          'Optimizer/GravitySigma':'0', # Disable imu constraints (we are already in 2D)
          'wait_imu_to_init':True}]
    # base_link -> camera_link = +8.6 CM in Z

    parameters2 = parameters.copy()
    parameters2.append({ # \/ \/ For node package='rtabmap_util', executable='obstacles_detection' \/ \/
                'Mem/IncrementalMemory':'True', # default: False @todo test 
                'Mem/InitWMWithAllNodes':'True'})

    remappings=[
          ('imu', '/imu/data'),
        #   ('rgb/image', '/camera/color/image_raw'),
        #   ('rgb/camera_info', '/camera/aligned_depth_to_color/camera_info'), # X
        #   ('depth/image', '/camera/aligned_depth_to_color/image_raw')]
        #   ('rgb/image', '/camera/infra1/image_rect_raw'),
        #   ('rgb/camera_info', '/camera/depth/camera_info'), # X
        #   ('depth/image', '/camera/depth/image_rect_raw')]
          ('rgb/image', '/camera/infra1/image_rect_raw'),
          ('rgb/camera_info', '/camera/infra1/camera_info'),
          ('depth/image', '/camera/depth/image_rect_raw')]

    # # load interbot URDF (launched by odrive_botwheel_explorer.launch.py)
    # pkg_share = FindPackageShare(package='sam_bot_description').find('sam_bot_description')
    # default_model_path = os.path.join(pkg_share, 'src', 'description', 'sam_bot_description.urdf')

    return LaunchDescription([

        # load interbot URDF (launched by odrive_botwheel_explorer.launch.py)
        # DeclareLaunchArgument(name='model', default_value=default_model_path, description='Absolute path to robot model file'),
        # Node(
        #     package='robot_state_publisher',
        #     executable='robot_state_publisher',
        #     parameters=[{'robot_description': Command(['xacro ', LaunchConfiguration('model')])}]
        # ),
        # Node( 
        #     package='joint_state_publisher',
        #     executable='joint_state_publisher',
        #     name='joint_state_publisher',
        #     parameters=[{'robot_description': Command(['xacro ', default_model_path])}]
        # ),

        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Launch in localization mode.'),

        # Launch arguments
        DeclareLaunchArgument(
            'unite_imu_method', default_value='2',
            description='0-None, 1-copy, 2-linear_interpolation. Use unite_imu_method:="1" if imu topics stop being published.'),

        # Realsense IR emitter, disable if using infrared image for visual odometry
        SetParameter(name='depth_module.emitter_enabled', value=0),

        # Launch camera driver
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('realsense2_camera'), 'launch'),
                '/rs_launch.py']),
                launch_arguments={'camera_namespace': '',
                                  'json_file_path': '/home/xu22pc/dev/rtabmap_ws2/d435i_high_accuracy_preset.json',
                                  'enable_gyro': 'true',
                                  'enable_accel': 'true',
                                  'unite_imu_method': LaunchConfiguration('unite_imu_method'),
                                  'enable_depth': 'true',
                                  'enable_infra': 'true',
                                  'enable_infra1': 'true',
                                  'enable_infra2': 'true',
                                  'enable_sync': 'true',
                                  'depth_module.enable_auto_exposure': 'true',
                                  'depth_module.exposure': '3500',
                                  'align_depth.enable': 'true'}.items(),
        ),

        Node(
            package='rtabmap_odom', executable='rgbd_odometry', output='screen',
            parameters=parameters,
            remappings=remappings),

        # SLAM mode:
        Node(
            condition=UnlessCondition(localization),
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=parameters,
            remappings=remappings,
            arguments=['']),
            # arguments=['-d']), # This will delete the previous database (~/.ros/rtabmap.db)

        # Localization mode:
        Node(
            condition=IfCondition(localization),
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=parameters,
            remappings=remappings),

        Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=parameters,
            remappings=remappings),
        
        # Compute quaternion of the IMU
        Node(
            package='imu_filter_madgwick', executable='imu_filter_madgwick_node', output='screen',
            parameters=[{'use_mag': False, 
                         'world_frame':'enu', 
                         'publish_tf':False}],
            remappings=[('imu/data_raw', '/camera/imu')]),


        

       
        # Obstacle detection with the camera for nav2 local costmap.
        # First, we need to convert depth image to a point cloud.
        # Second, we segment the floor from the obstacles.
        Node(
            package='rtabmap_util', executable='point_cloud_xyz', output='screen',
            parameters=[{'decimation': 2,
                         'max_depth': 3.0,
                         'voxel_size': 0.02}],
            # remappings=[('depth/image', '/camera/depth/image_raw'),
            remappings=[('depth/image', '/camera/depth/image_rect_raw'),
                        ('depth/camera_info', '/camera/depth/camera_info'),
                        ('cloud', '/camera/cloud')]),
        # Node(
        #     package='rtabmap_util', executable='obstacles_detection', output='screen',
        #     parameters=parameters2,
        #     # parameters=[parameters,   # Results in nested list which is not allowed
        #     #   {'Mem/IncrementalMemory':'False',
        #     #    'Mem/InitWMWithAllNodes':'True'}],
        #     remappings=[('cloud', '/camera/cloud'),
        #                 ('obstacles', '/camera/obstacles'),
        #                 ('ground', '/camera/ground')]),
    ])
