#include "mmp_rviz_plugins/map_selector_panel.hpp"

#include <QVBoxLayout>
#include <QHBoxLayout>

namespace mmp_rviz_plugins
{

MapSelectorPanel::MapSelectorPanel(QWidget * parent)
: rviz_common::Panel(parent),
  waiting_for_param_(false),
  waiting_for_service_(false)
{
  // Create layout
  QVBoxLayout * main_layout = new QVBoxLayout;

  // Title label
  QLabel * title_label = new QLabel("MMP Control Panel");
  QFont title_font = title_label->font();
  title_font.setPointSize(12);
  title_font.setBold(true);
  title_label->setFont(title_font);
  main_layout->addWidget(title_label);

  // Map selection section
  QLabel * map_label = new QLabel("Map Selection:");
  main_layout->addWidget(map_label);

  // Combo box for map selection
  map_combo_ = new QComboBox;
  // Maps will be loaded in onInitialize()
  main_layout->addWidget(map_combo_);

  // Load button
  load_button_ = new QPushButton("Load Map");
  connect(load_button_, &QPushButton::clicked, this, &MapSelectorPanel::onLoadMapClicked);
  main_layout->addWidget(load_button_);

  // Status label
  status_label_ = new QLabel("Current map: dokdo");
  status_label_->setStyleSheet("QLabel { color : green; }");
  main_layout->addWidget(status_label_);

  // Add stretch to push everything to the top
  main_layout->addStretch();

  setLayout(main_layout);

  // Create timers for async checking
  param_timer_ = new QTimer(this);
  connect(param_timer_, &QTimer::timeout, this, &MapSelectorPanel::checkParameterResult);

  service_timer_ = new QTimer(this);
  connect(service_timer_, &QTimer::timeout, this, &MapSelectorPanel::checkServiceResult);
}

MapSelectorPanel::~MapSelectorPanel()
{
}

void MapSelectorPanel::onInitialize()
{
  // Get the ROS node from the parent
  auto rviz_ros_node = getDisplayContext()->getRosNodeAbstraction();
  node_ = rviz_ros_node.lock()->get_raw_node();

  // Create service client
  map_change_client_ = node_->create_client<std_srvs::srv::Trigger>(
    "/terrain/change_map");

  // Create parameter client
  param_client_ = std::make_shared<rclcpp::AsyncParametersClient>(node_, "/terrain_publisher");

  // Load available maps from data directory
  loadAvailableMaps();

  status_label_->setText("Current map: dokdo");
  status_label_->setStyleSheet("QLabel { color : green; }");
}

void MapSelectorPanel::onLoadMapClicked()
{
  if (!node_) {
    status_label_->setText("Error: Node not initialized");
    status_label_->setStyleSheet("QLabel { color : red; }");
    return;
  }

  std::string selected_map = map_combo_->currentText().toStdString();

  status_label_->setText(QString("Loading %1...").arg(QString::fromStdString(selected_map)));
  status_label_->setStyleSheet("QLabel { color : blue; }");

  callMapChangeService(selected_map);
}

void MapSelectorPanel::loadAvailableMaps()
{
  // Get the package share directory path
  try {
    auto node_base = node_->get_node_base_interface();
    std::string package_share_dir;

    // Try to get mmp_terrain package share directory
    // In ROS2, we need to use ament_index to find package paths
    auto env_ament_prefix = std::getenv("AMENT_PREFIX_PATH");
    if (env_ament_prefix) {
      std::string ament_prefix(env_ament_prefix);
      // Parse the path - typically contains install paths separated by ':'
      size_t pos = 0;
      while (pos != std::string::npos) {
        size_t next_pos = ament_prefix.find(':', pos);
        std::string prefix_path = (next_pos != std::string::npos)
          ? ament_prefix.substr(pos, next_pos - pos)
          : ament_prefix.substr(pos);

        std::string potential_path = prefix_path + "/share/mmp_terrain/data";
        QDir data_dir(QString::fromStdString(potential_path));

        if (data_dir.exists()) {
          // Found the data directory!
          QStringList filters;
          filters << "*.tif";
          data_dir.setNameFilters(filters);

          QStringList tif_files = data_dir.entryList(QDir::Files | QDir::Readable, QDir::Name);

          if (!tif_files.isEmpty()) {
            map_combo_->clear();

            for (const QString & file : tif_files) {
              // Remove .tif extension
              QString map_name = file.left(file.lastIndexOf('.'));
              map_combo_->addItem(map_name);
              RCLCPP_INFO(node_->get_logger(), "Found map: %s", map_name.toStdString().c_str());
            }

            // Set default to dokdo if available
            int dokdo_index = map_combo_->findText("dokdo");
            if (dokdo_index >= 0) {
              map_combo_->setCurrentIndex(dokdo_index);
            }

            RCLCPP_INFO(node_->get_logger(), "Loaded %d maps from %s",
                       tif_files.size(), potential_path.c_str());
            return;
          }
        }

        pos = (next_pos != std::string::npos) ? next_pos + 1 : std::string::npos;
      }
    }

    // Fallback: add default maps
    RCLCPP_WARN(node_->get_logger(), "Could not find mmp_terrain data directory, using defaults");
    map_combo_->addItem("dokdo");
    map_combo_->addItem("jeju");
    map_combo_->addItem("seoul");
    map_combo_->setCurrentIndex(0);

  } catch (const std::exception & e) {
    RCLCPP_ERROR(node_->get_logger(), "Error loading maps: %s", e.what());
    // Fallback: add default maps
    map_combo_->addItem("dokdo");
    map_combo_->addItem("jeju");
    map_combo_->addItem("seoul");
    map_combo_->setCurrentIndex(0);
  }
}

void MapSelectorPanel::callMapChangeService(const std::string & map_name)
{
  if (waiting_for_param_ || waiting_for_service_) {
    status_label_->setText("Error: Already processing a request");
    status_label_->setStyleSheet("QLabel { color : orange; }");
    return;
  }

  if (!map_change_client_->service_is_ready()) {
    status_label_->setText("Error: Service not available");
    status_label_->setStyleSheet("QLabel { color : red; }");
    RCLCPP_ERROR(node_->get_logger(), "Map change service not available");
    return;
  }

  current_map_name_ = map_name;
  waiting_for_param_ = true;

  // Set parameter asynchronously
  param_future_ = param_client_->set_parameters({
    rclcpp::Parameter("world", map_name)
  });

  // Start timer to check result (100ms interval)
  param_timer_->start(100);
}

void MapSelectorPanel::checkParameterResult()
{
  if (!waiting_for_param_) {
    param_timer_->stop();
    return;
  }

  // Check if future is ready (non-blocking)
  if (param_future_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
    param_timer_->stop();
    waiting_for_param_ = false;

    try {
      auto results = param_future_.get();
      if (!results.empty() && results[0].successful) {
        RCLCPP_INFO(node_->get_logger(), "Parameter set successfully, calling service...");

        // Now call the service to reload the map
        waiting_for_service_ = true;
        auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
        service_future_ = map_change_client_->async_send_request(request);

        // Start service timer
        service_timer_->start(100);
      } else {
        status_label_->setText("Error: Failed to set parameter");
        status_label_->setStyleSheet("QLabel { color : red; }");
        RCLCPP_ERROR(node_->get_logger(), "Failed to set parameter");
      }
    } catch (const std::exception & e) {
      status_label_->setText("Error: Exception in parameter setting");
      status_label_->setStyleSheet("QLabel { color : red; }");
      RCLCPP_ERROR(node_->get_logger(), "Exception: %s", e.what());
    }
  }
}

void MapSelectorPanel::checkServiceResult()
{
  if (!waiting_for_service_) {
    service_timer_->stop();
    return;
  }

  // Check if future is ready (non-blocking)
  if (service_future_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
    service_timer_->stop();
    waiting_for_service_ = false;

    try {
      auto result = service_future_.get();
      if (result->success) {
        status_label_->setText(QString("Loaded: %1").arg(QString::fromStdString(current_map_name_)));
        status_label_->setStyleSheet("QLabel { color : green; }");
        RCLCPP_INFO(node_->get_logger(), "Successfully loaded map: %s", current_map_name_.c_str());
      } else {
        status_label_->setText("Error: Failed to load map");
        status_label_->setStyleSheet("QLabel { color : red; }");
        RCLCPP_ERROR(node_->get_logger(), "Failed to load map: %s", result->message.c_str());
      }
    } catch (const std::exception & e) {
      status_label_->setText("Error: Service call failed");
      status_label_->setStyleSheet("QLabel { color : red; }");
      RCLCPP_ERROR(node_->get_logger(), "Service call exception: %s", e.what());
    }
  }
}

}  // namespace mmp_rviz_plugins

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(mmp_rviz_plugins::MapSelectorPanel, rviz_common::Panel)
