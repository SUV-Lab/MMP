#ifndef MMP_RVIZ_PLUGINS__TRAJECTORY_COMMAND_PANEL_HPP_
#define MMP_RVIZ_PLUGINS__TRAJECTORY_COMMAND_PANEL_HPP_

#include <QSpinBox>
#include <QDoubleSpinBox>
#include <QComboBox>
#include <QPushButton>
#include <QVBoxLayout>
#include <QLabel>
#include <QLineEdit>

#include "rclcpp/rclcpp.hpp"
#include "rviz_common/panel.hpp"
#include "rviz_common/display_context.hpp"
#include "rviz_common/ros_integration/ros_node_abstraction.hpp"
#include "rviz_common/tool_manager.hpp"
#include "formation_msgs/msg/trajectory_command.hpp"
#include "geometry_msgs/msg/point_stamped.hpp"

namespace mmp_rviz_plugins
{

class TrajectoryCommandPanel : public rviz_common::Panel
{
  Q_OBJECT

public:
  explicit TrajectoryCommandPanel(QWidget * parent = nullptr);
  virtual ~TrajectoryCommandPanel();

  virtual void onInitialize() override;

protected Q_SLOTS:
  void onSetStartPointClicked();
  void onSetGoalPointClicked();
  void onStartTrajectoryClicked();

private:
  void clickedPointCallback(const geometry_msgs::msg::PointStamped::SharedPtr msg);
  void publishTrajectoryCommand();
  void updateStartPointLabel();
  void updateGoalPointLabel();

  // UI components
  QSpinBox * num_drones_spin_;
  QComboBox * formation_type_combo_;
  QDoubleSpinBox * formation_scale_spin_;

  QPushButton * set_start_button_;
  QPushButton * set_goal_button_;
  QPushButton * start_trajectory_button_;

  QLabel * start_point_label_;
  QLabel * goal_point_label_;
  QLabel * status_label_;

  // ROS components
  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<formation_msgs::msg::TrajectoryCommand>::SharedPtr trajectory_cmd_pub_;
  rclcpp::Subscription<geometry_msgs::msg::PointStamped>::SharedPtr clicked_point_sub_;

  // State
  geometry_msgs::msg::Point start_point_;
  geometry_msgs::msg::Point goal_point_;
  bool start_point_set_;
  bool goal_point_set_;
  bool waiting_for_start_click_;
  bool waiting_for_goal_click_;
};

}  // namespace mmp_rviz_plugins

#endif  // MMP_RVIZ_PLUGINS__TRAJECTORY_COMMAND_PANEL_HPP_
