cmake_minimum_required(VERSION 3.8)
project(mmp_rviz_plugins)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rviz_common REQUIRED)
find_package(rviz_rendering REQUIRED)
find_package(rviz_default_plugins REQUIRED)
find_package(pluginlib REQUIRED)
find_package(std_srvs REQUIRED)
find_package(formation_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(Qt5 REQUIRED COMPONENTS Widgets)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Include directories
include_directories(
  include
  ${Qt5Widgets_INCLUDE_DIRS}
)

# Generate moc file for the headers
qt5_wrap_cpp(MOC_FILES
  include/mmp_rviz_plugins/map_selector_panel.hpp
  include/mmp_rviz_plugins/trajectory_command_panel.hpp
  include/mmp_rviz_plugins/point_picker_tool.hpp
)

# RViz panels and tools library
add_library(${PROJECT_NAME} SHARED
  src/map_selector_panel.cpp
  src/trajectory_command_panel.cpp
  src/point_picker_tool.cpp
  ${MOC_FILES}
)

ament_target_dependencies(${PROJECT_NAME}
  rclcpp
  rviz_common
  rviz_rendering
  rviz_default_plugins
  pluginlib
  std_srvs
  formation_msgs
  geometry_msgs
)

target_link_libraries(${PROJECT_NAME}
  Qt5::Widgets
)

# Install library
install(TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Install plugin description
install(FILES
  plugins/plugin_description.xml
  DESTINATION share/${PROJECT_NAME}/plugins
)

# Install header files
install(DIRECTORY include/
  DESTINATION include
)

pluginlib_export_plugin_description_file(rviz_common plugins/plugin_description.xml)

ament_export_include_directories(include)
ament_export_targets(${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(
  rclcpp
  rviz_common
  rviz_rendering
  rviz_default_plugins
  pluginlib
  std_srvs
  formation_msgs
  geometry_msgs
  Qt5
)

ament_package()
