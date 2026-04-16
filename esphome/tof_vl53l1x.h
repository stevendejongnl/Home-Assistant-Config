#include "esphome.h"
#include <Wire.h>
#include <VL53L1X.h>

VL53L1X tof_sensor;

class TOFDistanceSensor : public PollingComponent, public Sensor {
 public:
  TOFDistanceSensor() : PollingComponent(300) {}

  void setup() override {
    Wire.begin();
    Wire.setClock(400000);

    tof_sensor.setTimeout(500);
    if (!tof_sensor.init()) {
      ESP_LOGE("TOF", "Failed to initialize VL53L1X sensor!");
      this->mark_failed();
      return;
    }

    tof_sensor.setDistanceMode(VL53L1X::Medium);
    tof_sensor.setMeasurementTimingBudget(50000);
    tof_sensor.startContinuous(50);
    ESP_LOGI("TOF", "VL53L1X initialized successfully");
  }

  void update() override {
    uint16_t mm = tof_sensor.read(false);
    if (tof_sensor.timeoutOccurred()) {
      ESP_LOGW("TOF", "Timeout during read");
      this->publish_state(NAN);
    } else {
      float meters = mm / 1000.0f;
      ESP_LOGD("TOF", "Distance: %d mm (%.3f m)", mm, meters);
      this->publish_state(meters);
    }
  }
};
