#pragma once
#include "esphome/core/component.h"
#include "esphome/components/sensor/sensor.h"
#include <VL53L1X.h>

namespace esphome {
namespace tof_vl53l1x {

class TOFSensor : public sensor::Sensor, public PollingComponent {
 public:
  TOFSensor() : PollingComponent(300) {}

  void setup() override {
    sensor_.setTimeout(500);
    if (!sensor_.init()) {
      ESP_LOGE("TOF", "Failed to initialize VL53L1X!");
      this->mark_failed();
      return;
    }
    sensor_.setDistanceMode(VL53L1X::Medium);
    sensor_.setMeasurementTimingBudget(50000);
    sensor_.startContinuous(50);
    ESP_LOGI("TOF", "VL53L1X initialized successfully");
  }

  void update() override {
    uint16_t mm = sensor_.read(false);
    if (sensor_.timeoutOccurred()) {
      ESP_LOGW("TOF", "Sensor timeout");
      this->publish_state(NAN);
    } else {
      this->publish_state(mm / 1000.0f);
    }
  }

 private:
  VL53L1X sensor_;
};

}  // namespace tof_vl53l1x
}  // namespace esphome
