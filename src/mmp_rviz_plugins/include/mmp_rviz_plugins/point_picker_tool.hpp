#ifndef MMP_RVIZ_PLUGINS__POINT_PICKER_TOOL_HPP_
#define MMP_RVIZ_PLUGINS__POINT_PICKER_TOOL_HPP_

#include "rclcpp/rclcpp.hpp"
#include "rviz_common/tool.hpp"
#include "rviz_common/display_context.hpp"
#include "rviz_common/viewport_mouse_event.hpp"
#include "geometry_msgs/msg/point_stamped.hpp"

#include <Ogre.h>

namespace mmp_rviz_plugins
{

class PointPickerTool : public rviz_common::Tool
{
  Q_OBJECT

public:
  PointPickerTool();
  virtual ~PointPickerTool();

  virtual void onInitialize() override;
  virtual void activate() override;
  virtual void deactivate() override;

  virtual int processMouseEvent(rviz_common::ViewportMouseEvent & event) override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<geometry_msgs::msg::PointStamped>::SharedPtr clicked_point_pub_;

  Ogre::Plane ground_plane_;
};

}  // namespace mmp_rviz_plugins

#endif  // MMP_RVIZ_PLUGINS__POINT_PICKER_TOOL_HPP_
