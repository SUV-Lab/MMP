#include "mmp_rviz_plugins/point_picker_tool.hpp"
#include "rviz_common/viewport_mouse_event.hpp"
#include "rviz_common/render_panel.hpp"
#include "rviz_common/display_context.hpp"
#include "rviz_common/ros_integration/ros_node_abstraction.hpp"
#include "rviz_common/view_manager.hpp"

namespace mmp_rviz_plugins
{

PointPickerTool::PointPickerTool()
: ground_plane_(Ogre::Vector3::UNIT_Z, 0.0)  // XY plane at z=0
{
}

PointPickerTool::~PointPickerTool()
{
}

void PointPickerTool::onInitialize()
{
  // Get ROS node
  auto rviz_ros_node = context_->getRosNodeAbstraction();
  node_ = rviz_ros_node.lock()->get_raw_node();

  // Create publisher for clicked points
  clicked_point_pub_ = node_->create_publisher<geometry_msgs::msg::PointStamped>(
    "/clicked_point", 10);

  RCLCPP_INFO(node_->get_logger(), "PointPickerTool initialized");
}

void PointPickerTool::activate()
{
  RCLCPP_DEBUG(node_->get_logger(), "PointPickerTool activated");
}

void PointPickerTool::deactivate()
{
  RCLCPP_DEBUG(node_->get_logger(), "PointPickerTool deactivated");
}

int PointPickerTool::processMouseEvent(rviz_common::ViewportMouseEvent & event)
{
  // Only process left mouse button clicks
  if (event.leftDown())
  {
    // Get the camera from the current view controller
    auto view_controller = context_->getViewManager()->getCurrent();
    if (!view_controller)
    {
      RCLCPP_ERROR(node_->get_logger(), "View controller is null");
      return 0;
    }

    Ogre::Camera* camera = view_controller->getCamera();
    if (!camera)
    {
      RCLCPP_ERROR(node_->get_logger(), "Camera is null");
      return 0;
    }

    // Get mouse position in viewport coordinates (0-1 range)
    int width = context_->getViewManager()->getRenderPanel()->width();
    int height = context_->getViewManager()->getRenderPanel()->height();

    float x = static_cast<float>(event.x) / static_cast<float>(width);
    float y = static_cast<float>(event.y) / static_cast<float>(height);

    // Create a ray from camera through mouse position
    Ogre::Ray ray = camera->getCameraToViewportRay(x, y);

    // Intersect ray with ground plane (z=0)
    std::pair<bool, Ogre::Real> result = ray.intersects(ground_plane_);

    if (result.first)
    {
      // Get the intersection point
      Ogre::Vector3 intersection = ray.getPoint(result.second);

      // Publish the clicked point
      auto msg = geometry_msgs::msg::PointStamped();
      msg.header.stamp = node_->now();
      msg.header.frame_id = context_->getFixedFrame().toStdString();
      msg.point.x = intersection.x;
      msg.point.y = intersection.y;
      msg.point.z = 0.0;  // Force z=0 for ground plane

      clicked_point_pub_->publish(msg);

      RCLCPP_INFO(node_->get_logger(),
        "Clicked point: (%.2f, %.2f, %.2f)",
        msg.point.x, msg.point.y, msg.point.z);
    }
  }

  return 0;
}

}  // namespace mmp_rviz_plugins

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(mmp_rviz_plugins::PointPickerTool, rviz_common::Tool)
