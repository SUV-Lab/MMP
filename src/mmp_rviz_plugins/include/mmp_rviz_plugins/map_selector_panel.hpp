#ifndef MMP_RVIZ_PLUGINS__MAP_SELECTOR_PANEL_HPP_
#define MMP_RVIZ_PLUGINS__MAP_SELECTOR_PANEL_HPP_

#include <QComboBox>
#include <QPushButton>
#include <QVBoxLayout>
#include <QLabel>
#include <QTimer>
#include <QDir>

#include "rclcpp/rclcpp.hpp"
#include "rviz_common/panel.hpp"
#include "rviz_common/display_context.hpp"
#include "rviz_common/ros_integration/ros_node_abstraction.hpp"
#include "std_srvs/srv/trigger.hpp"

namespace mmp_rviz_plugins
{

class MapSelectorPanel : public rviz_common::Panel
{
  Q_OBJECT

public:
  explicit MapSelectorPanel(QWidget * parent = nullptr);
  virtual ~MapSelectorPanel();

  virtual void onInitialize() override;

protected Q_SLOTS:
  void onLoadMapClicked();

private Q_SLOTS:
  void checkParameterResult();
  void checkServiceResult();

private:
  void callMapChangeService(const std::string & map_name);
  void loadAvailableMaps();

  QComboBox * map_combo_;
  QPushButton * load_button_;
  QLabel * status_label_;
  QTimer * param_timer_;
  QTimer * service_timer_;

  rclcpp::Node::SharedPtr node_;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr map_change_client_;
  std::shared_ptr<rclcpp::AsyncParametersClient> param_client_;

  std::shared_future<std::vector<rcl_interfaces::msg::SetParametersResult>> param_future_;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedFuture service_future_;
  std::string current_map_name_;
  bool waiting_for_param_;
  bool waiting_for_service_;
};

}  // namespace mmp_rviz_plugins

#endif  // MMP_RVIZ_PLUGINS__MAP_SELECTOR_PANEL_HPP_
