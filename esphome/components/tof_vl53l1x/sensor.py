import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import STATE_CLASS_MEASUREMENT, UNIT_METER

tof_ns = cg.esphome_ns.namespace("tof_vl53l1x")
TOFSensor = tof_ns.class_("TOFSensor", sensor.Sensor, cg.PollingComponent)

CONFIG_SCHEMA = sensor.sensor_schema(
    TOFSensor,
    unit_of_measurement=UNIT_METER,
    accuracy_decimals=2,
    state_class=STATE_CLASS_MEASUREMENT,
).extend(cv.polling_component_schema("300ms"))

async def to_code(config):
    var = await sensor.new_sensor(config)
    await cg.register_component(var, config)
    cg.add_library("pololu/VL53L1X", None)
