from setuptools import find_packages, setup

package_name = 'my_nav2_launch'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/navigation_launch.py']),
        ('share/' + package_name + '/launch', ['launch/navigation_dock_launch.py']),
        ('share/' + package_name + '/launch', ['launch/navigation_launch.tw9.py']),
        ('share/' + package_name + '/launch', ['launch/collision_monitor_node.launch.py']),
        ('share/' + package_name + '/params', ['params/nova_carter_docking.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='xu22pc',
    maintainer_email='60508542+Ab-Tx@users.noreply.github.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
    
)



