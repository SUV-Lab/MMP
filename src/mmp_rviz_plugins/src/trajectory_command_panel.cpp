#include "mmp_rviz_plugins/trajectory_command_panel.hpp"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QGroupBox>

namespace mmp_rviz_plugins
{

TrajectoryCommandPanel::TrajectoryCommandPanel(QWidget * parent)
: rviz_common::Panel(parent),
  start_point_set_(false),
  goal_point_set_(false),
  waiting_for_start_click_(false),
  waiting_for_goal_click_(false)
{
  // Initialize points to zero
  start_point_.x = 0.0;
  start_point_.y = 0.0;
  start_point_.z = 0.0;

  goal_point_.x = 0.0;
  goal_point_.y = 0.0;
  goal_point_.z = 0.0;

  // Create main layout
  QVBoxLayout * main_layout = new QVBoxLayout;

  // Title
  QLabel * title_label = new QLabel("Trajectory Command Panel");
  QFont title_font = title_label->font();
  title_font.setPointSize(12);
  title_font.setBold(true);
  title_label->setFont(title_font);
  main_layout->addWidget(title_label);

  // Configuration group
  QGroupBox * config_group = new QGroupBox("Configuration");
  QGridLayout * config_layout = new QGridLayout;

  // Number of drones (fixed to 1)
  QLabel * num_drones_label = new QLabel("Number of Drones:");
  num_drones_spin_ = new QSpinBox;
  num_drones_spin_->setMinimum(1);
  num_drones_spin_->setMaximum(10);
  num_drones_spin_->setValue(1);
  num_drones_spin_->setEnabled(false);  // Fixed value
  config_layout->addWidget(num_drones_label, 0, 0);
  config_layout->addWidget(num_drones_spin_, 0, 1);

  // Formation type (fixed to "none")
  QLabel * formation_type_label = new QLabel("Formation Type:");
  formation_type_combo_ = new QComboBox;
  formation_type_combo_->addItem("none");
  formation_type_combo_->addItem("line");
  formation_type_combo_->addItem("v_shape");
  formation_type_combo_->addItem("triangle");
  formation_type_combo_->setCurrentIndex(0);
  formation_type_combo_->setEnabled(false);  // Fixed value
  config_layout->addWidget(formation_type_label, 1, 0);
  config_layout->addWidget(formation_type_combo_, 1, 1);

  // Formation scale (fixed to 0.0)
  QLabel * formation_scale_label = new QLabel("Formation Scale:");
  formation_scale_spin_ = new QDoubleSpinBox;
  formation_scale_spin_->setMinimum(0.0);
  formation_scale_spin_->setMaximum(10.0);
  formation_scale_spin_->setSingleStep(0.1);
  formation_scale_spin_->setValue(0.0);
  formation_scale_spin_->setEnabled(false);  // Fixed value
  config_layout->addWidget(formation_scale_label, 2, 0);
  config_layout->addWidget(formation_scale_spin_, 2, 1);

  config_group->setLayout(config_layout);
  main_layout->addWidget(config_group);

  // Start point group
  QGroupBox * start_group = new QGroupBox("Start Point");
  QVBoxLayout * start_layout = new QVBoxLayout;

  set_start_button_ = new QPushButton("🎯 Set Start Point");
  set_start_button_->setStyleSheet("QPushButton { padding: 10px; font-size: 11pt; }");
  connect(set_start_button_, &QPushButton::clicked, this, &TrajectoryCommandPanel::onSetStartPointClicked);
  start_layout->addWidget(set_start_button_);

  start_point_label_ = new QLabel("Start: Not Set");
  start_point_label_->setStyleSheet("QLabel { color: gray; }");
  start_layout->addWidget(start_point_label_);

  start_group->setLayout(start_layout);
  main_layout->addWidget(start_group);

  // Goal point group
  QGroupBox * goal_group = new QGroupBox("Goal Point");
  QVBoxLayout * goal_layout = new QVBoxLayout;

  set_goal_button_ = new QPushButton("🎯 Set Goal Point");
  set_goal_button_->setStyleSheet("QPushButton { padding: 10px; font-size: 11pt; }");
  connect(set_goal_button_, &QPushButton::clicked, this, &TrajectoryCommandPanel::onSetGoalPointClicked);
  goal_layout->addWidget(set_goal_button_);

  goal_point_label_ = new QLabel("Goal: Not Set");
  goal_point_label_->setStyleSheet("QLabel { color: gray; }");
  goal_layout->addWidget(goal_point_label_);

  goal_group->setLayout(goal_layout);
  main_layout->addWidget(goal_group);

  // Start trajectory button
  start_trajectory_button_ = new QPushButton("▶ START TRAJECTORY");
  start_trajectory_button_->setStyleSheet(
    "QPushButton { "
    "  background-color: #4CAF50; "
    "  color: white; "
    "  padding: 15px; "
    "  font-size: 12pt; "
    "  font-weight: bold; "
    "}"
    "QPushButton:hover { "
    "  background-color: #45a049; "
    "}"
    "QPushButton:disabled { "
    "  background-color: #cccccc; "
    "  color: #666666; "
    "}"
  );
  start_trajectory_button_->setEnabled(false);
  connect(start_trajectory_button_, &QPushButton::clicked, this, &TrajectoryCommandPanel::onStartTrajectoryClicked);
  main_layout->addWidget(start_trajectory_button_);

  // Status label
  status_label_ = new QLabel("Status: Waiting for points...");
  status_label_->setStyleSheet("QLabel { color: gray; padding: 5px; }");
  main_layout->addWidget(status_label_);

  // Add stretch to push everything to the top
  main_layout->addStretch();

  setLayout(main_layout);
}

TrajectoryCommandPanel::~TrajectoryCommandPanel()
{
}

void TrajectoryCommandPanel::onInitialize()
{
  // Get ROS node from parent
  auto rviz_ros_node = getDisplayContext()->getRosNodeAbstraction();
  node_ = rviz_ros_node.lock()->get_raw_node();

  // Create publisher for trajectory command (V1 for single drone)
  trajectory_cmd_pub_ = node_->create_publisher<formation_msgs::msg::TrajectoryCommand>(
    "/V1/trajectory_command", 10);

  // Subscribe to clicked point topic from RViz
  clicked_point_sub_ = node_->create_subscription<geometry_msgs::msg::PointStamped>(
    "/clicked_point",
    10,
    std::bind(&TrajectoryCommandPanel::clickedPointCallback, this, std::placeholders::_1));

  RCLCPP_INFO(node_->get_logger(), "TrajectoryCommandPanel initialized");
}

void TrajectoryCommandPanel::onSetStartPointClicked()
{
  waiting_for_start_click_ = true;
  waiting_for_goal_click_ = false;

  set_start_button_->setStyleSheet(
    "QPushButton { "
    "  background-color: #2196F3; "
    "  color: white; "
    "  padding: 10px; "
    "  font-size: 11pt; "
    "}"
  );
  set_goal_button_->setStyleSheet("QPushButton { padding: 10px; font-size: 11pt; }");

  status_label_->setText("Status: Click on the map to set START point...");
  status_label_->setStyleSheet("QLabel { color: blue; padding: 5px; font-weight: bold; }");

  RCLCPP_INFO(node_->get_logger(), "Waiting for start point click...");
}

void TrajectoryCommandPanel::onSetGoalPointClicked()
{
  waiting_for_start_click_ = false;
  waiting_for_goal_click_ = true;

  set_start_button_->setStyleSheet("QPushButton { padding: 10px; font-size: 11pt; }");
  set_goal_button_->setStyleSheet(
    "QPushButton { "
    "  background-color: #2196F3; "
    "  color: white; "
    "  padding: 10px; "
    "  font-size: 11pt; "
    "}"
  );

  status_label_->setText("Status: Click on the map to set GOAL point...");
  status_label_->setStyleSheet("QLabel { color: blue; padding: 5px; font-weight: bold; }");

  RCLCPP_INFO(node_->get_logger(), "Waiting for goal point click...");
}

void TrajectoryCommandPanel::onStartTrajectoryClicked()
{
  if (!start_point_set_ || !goal_point_set_) {
    status_label_->setText("Status: ERROR - Both points must be set!");
    status_label_->setStyleSheet("QLabel { color: red; padding: 5px; font-weight: bold; }");
    return;
  }

  publishTrajectoryCommand();

  status_label_->setText("Status: ✓ Trajectory command published!");
  status_label_->setStyleSheet("QLabel { color: green; padding: 5px; font-weight: bold; }");

  RCLCPP_INFO(node_->get_logger(),
    "Trajectory command published - Start: (%.2f, %.2f, %.2f), Goal: (%.2f, %.2f, %.2f)",
    start_point_.x, start_point_.y, start_point_.z,
    goal_point_.x, goal_point_.y, goal_point_.z);
}

void TrajectoryCommandPanel::clickedPointCallback(
  const geometry_msgs::msg::PointStamped::SharedPtr msg)
{
  // Block signals to batch UI updates
  setUpdatesEnabled(false);

  if (waiting_for_start_click_) {
    start_point_ = msg->point;
    start_point_set_ = true;
    waiting_for_start_click_ = false;

    set_start_button_->setStyleSheet("QPushButton { padding: 10px; font-size: 11pt; }");
    updateStartPointLabel();
    status_label_->setText("Status: ✓ Start point set!");
    status_label_->setStyleSheet("QLabel { color: green; padding: 5px; }");

    RCLCPP_INFO(node_->get_logger(), "Start point set: (%.2f, %.2f, %.2f)",
      start_point_.x, start_point_.y, start_point_.z);

    // Enable start button if both points are set
    if (start_point_set_ && goal_point_set_) {
      start_trajectory_button_->setEnabled(true);
    }
  }
  else if (waiting_for_goal_click_) {
    goal_point_ = msg->point;
    goal_point_set_ = true;
    waiting_for_goal_click_ = false;

    set_goal_button_->setStyleSheet("QPushButton { padding: 10px; font-size: 11pt; }");
    updateGoalPointLabel();
    status_label_->setText("Status: ✓ Goal point set!");
    status_label_->setStyleSheet("QLabel { color: green; padding: 5px; }");

    RCLCPP_INFO(node_->get_logger(), "Goal point set: (%.2f, %.2f, %.2f)",
      goal_point_.x, goal_point_.y, goal_point_.z);

    // Enable start button if both points are set
    if (start_point_set_ && goal_point_set_) {
      start_trajectory_button_->setEnabled(true);
    }
  }

  // Re-enable updates and refresh once
  setUpdatesEnabled(true);
}

void TrajectoryCommandPanel::publishTrajectoryCommand()
{
  auto msg = formation_msgs::msg::TrajectoryCommand();

  // Header
  msg.header.stamp = node_->now();
  msg.header.frame_id = "map";

  // Drone identification
  msg.drone_id = 0;  // V1 = drone_0
  msg.sequence = 0;
  msg.mission_id = "gui_mission";

  // Start and target positions
  msg.start_position = start_point_;
  msg.target_position = goal_point_;

  // Target velocity (zero for now)
  msg.target_velocity.x = 0.0;
  msg.target_velocity.y = 0.0;
  msg.target_velocity.z = 0.0;

  // Waypoints (just the goal point for direct trajectory)
  msg.waypoints.push_back(goal_point_);

  // Formation metadata (fixed values matching scenario_threat_zones.yaml)
  msg.formation_type = formation_type_combo_->currentText().toStdString();
  msg.formation_scale = formation_scale_spin_->value();

  // Formation offset (zero for single drone)
  msg.formation_offset.x = 0.0;
  msg.formation_offset.y = 0.0;
  msg.formation_offset.z = 0.0;

  // Formation pattern (empty for single drone with "none" formation)
  geometry_msgs::msg::Point pattern_point;
  pattern_point.x = 0.0;
  pattern_point.y = 0.0;
  pattern_point.z = 0.0;
  msg.formation_pattern.push_back(pattern_point);

  // Publish the message
  trajectory_cmd_pub_->publish(msg);
}

void TrajectoryCommandPanel::updateStartPointLabel()
{
  QString text = QString("Start: (%.2f, %.2f, %.2f)")
    .arg(start_point_.x, 0, 'f', 2)
    .arg(start_point_.y, 0, 'f', 2)
    .arg(start_point_.z, 0, 'f', 2);
  start_point_label_->setText(text);
  start_point_label_->setStyleSheet("QLabel { color: green; font-weight: bold; }");
}

void TrajectoryCommandPanel::updateGoalPointLabel()
{
  QString text = QString("Goal: (%.2f, %.2f, %.2f)")
    .arg(goal_point_.x, 0, 'f', 2)
    .arg(goal_point_.y, 0, 'f', 2)
    .arg(goal_point_.z, 0, 'f', 2);
  goal_point_label_->setText(text);
  goal_point_label_->setStyleSheet("QLabel { color: green; font-weight: bold; }");
}

}  // namespace mmp_rviz_plugins

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(mmp_rviz_plugins::TrajectoryCommandPanel, rviz_common::Panel)
