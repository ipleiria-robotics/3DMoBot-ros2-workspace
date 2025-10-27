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
#   $ ros2 launch rtabmap_examples realsense_d435i_stereo.launch.py

#   If an IMU is used, make sure TF between lidar/base frame and imu is
#     already calibrated. In this example, we assume the imu topic has 
#     already the orientation estimated, if not, you can use 
#     imu_filter_madgwick_node (with use_mag:=false publish_tf:=false)
#     and set imu_topic to output topic of the filter.
#
#   If a camera is used, make sure TF between lidar/base frame and camera is
#     already calibrated. To provide image data to this example, you should use
#     rtabmap_sync's rgbd_sync or stereo_sync node.

import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.substitutions import FindPackageShare

def launch_setup(context: LaunchContext, *args, **kwargs):
  
  frame_id = LaunchConfiguration('frame_id')
  
  imu_topic = LaunchConfiguration('imu_topic')
  imu_used =  imu_topic.perform(context) != ''
  
  rgbd_image_topic = LaunchConfiguration('rgbd_image_topic')
  rgbd_images_topic = LaunchConfiguration('rgbd_images_topic')
  rgbd_image_used =  rgbd_image_topic.perform(context) != '' or rgbd_images_topic.perform(context) != ''
  rgbd_cameras = 0 if rgbd_images_topic.perform(context) != '' else 1
  
  voxel_size = LaunchConfiguration('voxel_size')
  voxel_size_value = float(voxel_size.perform(context))
  
  use_sim_time = LaunchConfiguration('use_sim_time')
  
  lidar_topic = LaunchConfiguration('lidar_topic')
  lidar_topic_value = lidar_topic.perform(context)
  lidar_topic_deskewed = lidar_topic_value + "/deskewed"
  
  localization = LaunchConfiguration('localization').perform(context)
  localization = localization == 'true' or localization == 'True'
  
  deskewing = LaunchConfiguration('deskewing').perform(context)
  deskewing = deskewing == 'true' or deskewing == 'True'
  
  deskewing_slerp = LaunchConfiguration('deskewing_slerp').perform(context)
  deskewing_slerp = deskewing_slerp == 'true' or deskewing_slerp == 'True'
  
  fixed_frame_from_imu = False
  fixed_frame_id =  LaunchConfiguration('fixed_frame_id').perform(context)
  if not fixed_frame_id and imu_used:
    fixed_frame_from_imu = True
    fixed_frame_id = frame_id.perform(context) + "_stabilized"
  
  if not fixed_frame_id or not deskewing:
    lidar_topic_deskewed = lidar_topic
  
  # Rule of thumb:
  max_correspondence_distance = voxel_size_value * 10.0

  shared_parameters = {
    'use_sim_time': use_sim_time,
    'frame_id': frame_id,
    'qos': LaunchConfiguration('qos'),
    'approx_sync': rgbd_image_used,
    'wait_for_transform': 0.2,
    # RTAB-Map's internal parameters are strings:
    'Icp/PointToPlane': 'true',
    'Icp/Iterations': '10',
    'Icp/VoxelSize': str(voxel_size_value),
    'Icp/Epsilon': '0.001',
    'Icp/PointToPlaneK': '20',
    'Icp/PointToPlaneRadius': '0',
    'Icp/MaxTranslation': '3',
    'Icp/MaxCorrespondenceDistance': str(max_correspondence_distance),
    'Icp/Strategy': '1',
    'Icp/OutlierRatio': '0.7',
  }
  
  icp_odometry_parameters = {
    'expected_update_rate': LaunchConfiguration('expected_update_rate'),
    'deskewing': not fixed_frame_id and deskewing, # If fixed_frame_id is set, we do deskewing externally below
    'odom_frame_id': 'icp_odom',
    'guess_frame_id': fixed_frame_id,
    'deskewing_slerp': deskewing_slerp,
    # RTAB-Map's internal parameters are strings:
    'Odom/ScanKeyFrameThr': '0.4',
    'OdomF2M/ScanSubtractRadius': str(voxel_size_value),
    'OdomF2M/ScanMaxSize': '15000',
    'OdomF2M/BundleAdjustment': 'false',
    'Icp/CorrespondenceRatio': '0.01',
    'scan_cloud_max_points': 131072, # 128*1024 points
  }
  if imu_used:
    icp_odometry_parameters['wait_imu_to_init'] = True

  rtabmap_parameters = {
    'subscribe_depth': False, # False,
    'subscribe_rgb': False, # False,
    'subscribe_rgbd': True, # False,
    'subscribe_odom_info': True,
    'subscribe_scan_cloud': True,
    'map_frame_id': 'new_map',
    'odom_sensor_sync': True, # This will adjust camera position based on difference between lidar and camera stamps.
    # RTAB-Map's internal parameters are strings:
    'RGBD/ProximityMaxGraphDepth': '0',
    'RGBD/ProximityPathMaxNeighbors': '1',
    'RGBD/AngularUpdate': '0.05',
    'RGBD/LinearUpdate': '0.05',
    'RGBD/CreateOccupancyGrid': 'false',
    'Mem/NotLinkedNodesKept': 'false',
    'Mem/STMSize': '30',
    'Reg/Strategy': '2', # 1=Icp, 2=Icp+Visual, 3=Visual
    'sync_queue_size': 10,
    'topic_queue_size': 10,
    # 'Reg/Force3DoF': 'true',
    'Icp/CorrespondenceRatio': str(LaunchConfiguration('min_loop_closure_overlap').perform(context))
  }
  
  arguments = []
  if localization:
    rtabmap_parameters['Mem/IncrementalMemory'] = 'False'
    rtabmap_parameters['Mem/InitWMWithAllNodes'] = 'True'
  else:
    arguments.append('-d') # This will delete the previous database (~/.ros/rtabmap.db)
  
  remappings = [('odom', 'icp_odom')]
  if imu_used:
    remappings.append(('imu', LaunchConfiguration('imu_topic')))
  else:
    remappings.append(('imu', 'imu_not_used'))
  if rgbd_image_used:
    if rgbd_cameras == 1:
      remappings.append(('rgbd_image', LaunchConfiguration('rgbd_image_topic')))
    else:
      remappings.append(('rgbd_images', LaunchConfiguration('rgbd_images_topic')))
  
  
  # for rtabmap rgbd custom message:
  odom_parameters=[{
        # 'frame_id':'camera_link', #frame_id, #
        'approx_sync': rgbd_image_used, #'false',
        'approx_sync_max_interval': 0.01, # 10 ms
    }]
  odom_remappings=[
          ('rgb/image', '/camera/color/image_raw'),
          ('rgb/camera_info', '/camera/color/camera_info'),
          ('depth/image', '/camera/aligned_depth_to_color/image_raw')] #'/camera/depth/image_rect_raw')]

  nodes = [
    Node( # https://wiki.ros.org/rtabmap_sync#Published_Topics
      package='rtabmap_sync', executable='rgbd_sync', output='screen',
      parameters=odom_parameters,
      remappings=odom_remappings),

    Node(
      package='rtabmap_odom', executable='icp_odometry', output='screen',
      parameters=[shared_parameters, icp_odometry_parameters],
      remappings=remappings + [('scan_cloud', lidar_topic_deskewed)]),
    
    Node(
      package='rtabmap_slam', executable='rtabmap', output='screen',
      parameters=[shared_parameters, rtabmap_parameters, 
                  {'subscribe_rgbd': rgbd_image_used, 
                   'rgbd_cameras': rgbd_cameras}],
      remappings=remappings + [('scan_cloud', lidar_topic_deskewed)],
      arguments=arguments), 
  
    Node(
      package='rtabmap_viz', executable='rtabmap_viz', output='screen',
      parameters=[shared_parameters, rtabmap_parameters],
      remappings=remappings + [('scan_cloud', 'odom_filtered_input_scan')]),

    # (user added)
    # Compute quaternion of the IMU
    Node(
        package='imu_filter_madgwick', executable='imu_filter_madgwick_node', output='screen',
        parameters=[{'use_mag': False, 
                      'world_frame':'enu', 
                      'publish_tf':False}],
        remappings=[('imu/data_raw', '/ouster/imu')]),

        
  ]
  
  if fixed_frame_from_imu:
    # Create a stabilized base frame based on imu for lidar deskewing
    nodes.append(
      Node(
        package='rtabmap_util', executable='imu_to_tf', output='screen',
        parameters=[{
          'use_sim_time': use_sim_time,
          'fixed_frame_id': fixed_frame_id,
          'base_frame_id': frame_id,
          'wait_for_transform_duration': 0.001}],
        remappings=[('imu/data', imu_topic)]))

  if fixed_frame_id and deskewing:
    # Lidar deskewing
    nodes.append(
      Node(
        package='rtabmap_util', executable='lidar_deskewing', output='screen',
        parameters=[{
          'use_sim_time': use_sim_time,
          'fixed_frame_id': fixed_frame_id,
          'wait_for_transform': 0.2,
          'slerp': deskewing_slerp}],
        remappings=[
            ('input_cloud', lidar_topic)
        ])
    )
      
  return nodes
  
def generate_launch_description():

  # load interbot URDF
  pkg_share = FindPackageShare(package='sam_bot_description').find('sam_bot_description')
  default_model_path = os.path.join(pkg_share, 'src', 'description', 'sam_bot_description.urdf')
  return LaunchDescription([

    # load interbot URDF
    DeclareLaunchArgument(name='model', default_value=default_model_path, description='Absolute path to robot model file'),
    Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': Command(['xacro ', LaunchConfiguration('model')])}]
    ),
    Node( 
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'robot_description': Command(['xacro ', default_model_path])}]
    ),

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
                              'enable_gyro': 'false',
                              'enable_accel': 'false',
                              'unite_imu_method': LaunchConfiguration('unite_imu_method'),
                              'enable_depth': 'true',
                              'enable_infra': 'true',
                              'enable_infra1': 'true',
                              'enable_infra2': 'true',
                              'enable_sync': 'true',
                              'disparity_filter.enable': 'false',
                              'hdr_merge.enable': 'false',
                              'depth_module.hdr_enabled': 'false',
                              'align_depth.enable': 'true'}.items(),
    ),

    # Launch arguments
    DeclareLaunchArgument(
      'use_sim_time', default_value='false',
      description='Use simulated clock.'),
    
    DeclareLaunchArgument(
      'deskewing', default_value='true',
      description='Enable lidar deskewing.'),
    
    DeclareLaunchArgument(
      'frame_id', default_value='base_link', #'velodyne',
      description='Base frame of the robot.'),
    
    DeclareLaunchArgument(
      'fixed_frame_id', default_value='',
      description='Fixed frame used for lidar deskewing. If not set, we will generate one from IMU.'),
    
    DeclareLaunchArgument(
      'localization', default_value='false',
      description='Localization mode.'),

    DeclareLaunchArgument(
      'lidar_topic', default_value='/ouster/points', #'/velodyne_points',
      description='Name of the lidar PointCloud2 topic.'),

    DeclareLaunchArgument(
      'imu_topic', default_value='/imu/data',
      description='IMU topic (ignored if empty).'),
    
    DeclareLaunchArgument(
      'rgbd_image_topic', default_value='', #/camera/color/image_raw
      description='RGBD image topic (ignored if empty). Would be the output of a rtabmap_sync\'s rgbd_sync, stereo_sync or rgb_sync node.'),
    
    DeclareLaunchArgument(
      'rgbd_images_topic', default_value='',
      description='RGBD images topic (ignored if empty, override "rgbd_image_topic" if set). Would be the output of a rtabmap_sync\'s rgbdx_sync node.'),
    
    DeclareLaunchArgument(
      'expected_update_rate', default_value='10.0',
      description='Expected lidar frame rate. Ideally, set it slightly higher than actual frame rate, like 15 Hz for 10 Hz lidar scans.'),
    
    DeclareLaunchArgument(
      'voxel_size', default_value='0.1',
      description='Voxel size (m) of the downsampled lidar point cloud. For indoor, set it between 0.1 and 0.3. For outdoor, set it to 0.5 or over.'),
    
    DeclareLaunchArgument(
      'min_loop_closure_overlap', default_value='0.2',
      description='Minimum scan overlap pourcentage to accept a loop closure.'),
    
    DeclareLaunchArgument(
      'deskewing_slerp', default_value='true',
      description='Use fast slerp interpolation between first and last stamps of the scan for deskewing. It would less accruate than requesting TF for every points, but a lot faster. Enable this if the delay of the deskewed scan is significant larger than the original scan.'),

    DeclareLaunchArgument(
      'qos', default_value='1',
      description='Quality of Service: 0=system default, 1=reliable, 2=best effort.'),

    OpaqueFunction(function=launch_setup),
  ])

    
