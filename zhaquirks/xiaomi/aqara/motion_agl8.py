"""Quirk for Aqara Presence Multi-Sensor FP300 lumi.sensor_occupy.agl8."""

# ruff: noqa: D101, D102, D106, D107
import asyncio
from typing import Any, Final

from zigpy import types as t
from zigpy.quirks.v2 import QuirkBuilder, ReportingConfig
from zigpy.quirks.v2.homeassistant import (
    PERCENTAGE,
    EntityType,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfTime,
)
from zigpy.quirks.v2.homeassistant.binary_sensor import BinarySensorDeviceClass
from zigpy.quirks.v2.homeassistant.number import NumberDeviceClass
from zigpy.quirks.v2.homeassistant.sensor import SensorDeviceClass, SensorStateClass
from zigpy.typing import UNDEFINED, UndefinedType
from zigpy.zcl import foundation
from zigpy.zcl.foundation import BaseAttributeDefs, DataTypeId, ZCLAttributeDef

from zhaquirks import LocalDataCluster
from zhaquirks.xiaomi import (
    BATTERY_VOLTAGE_MV,
    XiaomiAqaraE1Cluster,
    XiaomiPowerConfiguration,
)

AQARA_MFG_CODE: Final = 0x115F
FP300_ATTR_BATTERY_VOLTAGE: Final = "0xff01-23"
FP300_ATTR_BATTERY_PERCENT: Final = "0xff01-24"  # unused, keep for future


class PresenceSensitivity(t.enum8):
    Low = 1
    Medium = 2
    High = 3


class PresenceDetectionMode(t.enum8):
    Both = 0
    Only_mmWave = 1
    Only_PIR = 2


class SamplingFrequency(t.enum8):
    Off = 0
    Low = 1
    Medium = 2
    High = 3
    Custom = 4


class ReportMode(t.enum8):
    Threshold = 1
    Interval = 2
    Threshold_and_interval = 3


class FP300PowerConfiguration(XiaomiPowerConfiguration):
    """Battery level based on voltage."""

    MIN_VOLTS_MV = 2800
    MAX_VOLTS_MV = 3000

    def battery_reported(self, voltage_mv: int) -> None:
        # FP300 reports voltage in mV
        self._update_attribute(self.BATTERY_VOLTAGE_ATTR, round(voltage_mv / 1000, 3))
        self._update_battery_percentage(voltage_mv)

    def battery_percent_reported(self, battery_percent: int) -> None:
        """Ignore buggy percentage reports from device."""
        pass


class AqaraFP300ManuCluster(XiaomiAqaraE1Cluster):
    """Aqara FP300 manufacturer cluster."""

    cluster_id = 0xFCC0
    ep_attribute = "aqara_fp300_manu"

    class AttributeDefs(XiaomiAqaraE1Cluster.AttributeDefs):
        # Presence / PIR
        presence: Final = ZCLAttributeDef(
            id=0x0142,
            type=t.Bool,
            zcl_type=DataTypeId.uint8,
            access="rp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        pir_detection: Final = ZCLAttributeDef(
            id=0x014D,
            type=t.Bool,
            zcl_type=DataTypeId.uint8,
            access="rp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        presence_detection_mode: Final = ZCLAttributeDef(
            id=0x0199,
            type=PresenceDetectionMode,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        absence_delay: Final = ZCLAttributeDef(
            id=0x0197,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        presence_sensitivity: Final = ZCLAttributeDef(
            id=0x010C,
            type=PresenceSensitivity,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        pir_detection_interval: Final = ZCLAttributeDef(
            id=0x014F,
            type=t.uint16_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # AI
        ai_interference_identification: Final = ZCLAttributeDef(
            id=0x015E,
            type=t.uint8_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        ai_sensitivity_adaptive: Final = ZCLAttributeDef(
            id=0x015D,
            type=t.uint8_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # Illuminance
        light_reporting_threshold: Final = ZCLAttributeDef(
            id=0x0195,
            type=t.uint16_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        light_sampling: Final = ZCLAttributeDef(
            id=0x0192,
            type=SamplingFrequency,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        light_reporting_mode: Final = ZCLAttributeDef(
            id=0x0196,
            type=ReportMode,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        light_sampling_period: Final = ZCLAttributeDef(
            id=0x0193,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        light_reporting_interval: Final = ZCLAttributeDef(
            id=0x0194,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # Temperature / humidity
        humidity_reporting_mode: Final = ZCLAttributeDef(
            id=0x016C,
            type=ReportMode,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        temp_reporting_threshold: Final = ZCLAttributeDef(
            id=0x0164,
            type=t.uint16_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        temp_humidity_sampling: Final = ZCLAttributeDef(
            id=0x0170,
            type=SamplingFrequency,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        humidity_reporting_interval: Final = ZCLAttributeDef(
            id=0x016A,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        temp_humidity_sampling_period: Final = ZCLAttributeDef(
            id=0x0162,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        temp_reporting_interval: Final = ZCLAttributeDef(
            id=0x0163,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        humidity_reporting_threshold: Final = ZCLAttributeDef(
            id=0x016B,
            type=t.uint16_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        temp_reporting_mode: Final = ZCLAttributeDef(
            id=0x0165,
            type=ReportMode,
            zcl_type=DataTypeId.uint8,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # LED
        led_schedule_time_raw: Final = ZCLAttributeDef(
            id=0x023E,
            type=t.uint32_t,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        led_off_schedule: Final = ZCLAttributeDef(
            id=0x0203,
            type=t.Bool,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # Buttons
        spatial_learning: Final = ZCLAttributeDef(
            id=0x0157,
            type=t.uint8_t,
            access="w",
            manufacturer_code=AQARA_MFG_CODE,
        )
        restart_device: Final = ZCLAttributeDef(
            id=0x00E8,
            type=t.Bool,
            access="w",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # Diagnostic
        target_distance: Final = ZCLAttributeDef(
            id=0x015F,
            type=t.uint32_t,
            access="rp",
            manufacturer_code=AQARA_MFG_CODE,
        )
        track_target_distance: Final = ZCLAttributeDef(
            id=0x0198,
            type=t.uint8_t,
            access="w",
            manufacturer_code=AQARA_MFG_CODE,
        )

        # Raw
        detection_range_raw: Final = ZCLAttributeDef(
            id=0x019A,
            type=t.LVBytes,
            access="rwp",
            manufacturer_code=AQARA_MFG_CODE,
        )

    def _update_attribute(self, attrid: int, value: Any) -> None:
        super()._update_attribute(attrid, value)

        if attrid == self.AttributeDefs.detection_range_raw.id:
            self.endpoint.fp300_detection_range.apply_raw(value)
        elif attrid == self.AttributeDefs.led_schedule_time_raw.id:
            self.endpoint.fp300_led_schedule.apply_raw(value)

    async def bind(self):
        result = await super().bind()

        # Initial sync for attrs not sent on join
        for attr_id in (
            self.AttributeDefs.detection_range_raw.id,
            self.AttributeDefs.led_schedule_time_raw.id,
        ):
            try:
                await self.read_attributes(
                    [attr_id],
                    allow_cache=False,
                    manufacturer=AQARA_MFG_CODE,
                )
            except Exception as exc:
                self.debug("Failed to read attr 0x%04X: %r", attr_id, exc)

        return result

    def _parse_aqara_attributes(self, value: Any) -> dict[str, Any]:
        attributes = super()._parse_aqara_attributes(value)

        if FP300_ATTR_BATTERY_VOLTAGE in attributes:
            attributes[BATTERY_VOLTAGE_MV] = attributes.pop(FP300_ATTR_BATTERY_VOLTAGE)

        return attributes


class FP300DetectionRangeCluster(LocalDataCluster):
    """Virtual cluster for detection range."""

    cluster_id = 0xFCF0
    ep_attribute = "fp300_detection_range"

    # Fallback when cache is empty before first successful read (All on)
    DEFAULT_MASK: Final = 0xFFFFFF
    # Detection range payload prefix
    PREFIX: Final = (0x0300).to_bytes(2, "little")
    # One zone = 4 bits
    ZONE_MASK: Final = 0x0F
    # Mask starts at byte 2
    MASK_OFFSET: Final = 2
    # Raw attr on ManuCluster
    RAW_ATTR: Final = AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id

    class AttributeDefs(BaseAttributeDefs):
        range_0_1m: Final = ZCLAttributeDef(
            id=0x0000,
            type=t.Bool,
            manufacturer_code=AQARA_MFG_CODE,
        )
        range_1_2m: Final = ZCLAttributeDef(
            id=0x0001,
            type=t.Bool,
            manufacturer_code=AQARA_MFG_CODE,
        )
        range_2_3m: Final = ZCLAttributeDef(
            id=0x0002,
            type=t.Bool,
            manufacturer_code=AQARA_MFG_CODE,
        )
        range_3_4m: Final = ZCLAttributeDef(
            id=0x0003,
            type=t.Bool,
            manufacturer_code=AQARA_MFG_CODE,
        )
        range_4_5m: Final = ZCLAttributeDef(
            id=0x0004,
            type=t.Bool,
            manufacturer_code=AQARA_MFG_CODE,
        )
        range_5_6m: Final = ZCLAttributeDef(
            id=0x0005,
            type=t.Bool,
            manufacturer_code=AQARA_MFG_CODE,
        )

    RANGE_MAP: Final = (
        (AttributeDefs.range_0_1m.id, 0),
        (AttributeDefs.range_1_2m.id, 4),
        (AttributeDefs.range_2_3m.id, 8),
        (AttributeDefs.range_3_4m.id, 12),
        (AttributeDefs.range_4_5m.id, 16),
        (AttributeDefs.range_5_6m.id, 20),
    )

    _SHIFT_BY_ID: Final = dict(RANGE_MAP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent overlapping writes
        self._write_mutex = asyncio.Lock()

    def _unpack_mask(self, raw: bytes) -> int:
        return int.from_bytes(raw[self.MASK_OFFSET : self.MASK_OFFSET + 3], "little")

    def apply_raw(self, raw: bytes) -> None:
        raw = bytes(raw)
        if len(raw) != 5:
            self.debug("Invalid detection_range_raw length: %d", len(raw))
            return

        mask = self._unpack_mask(raw)
        for attr_id, shift in self.RANGE_MAP:
            self._update_attribute(attr_id, bool(mask & (self.ZONE_MASK << shift)))

    async def write_attributes(
        self,
        attributes: dict[str | int | foundation.ZCLAttributeDef, Any],
        manufacturer: int | UndefinedType | None = UNDEFINED,
        **kwargs,
    ) -> list[list[foundation.WriteAttributesStatusRecord]]:
        async with self._write_mutex:
            resolved = {
                self.find_attribute(attr).id: value
                for attr, value in attributes.items()
            }

            raw = self.endpoint.aqara_fp300_manu.get(self.RAW_ATTR)

            mask = self.DEFAULT_MASK
            if raw is not None:
                raw = bytes(raw)
                if len(raw) == 5:
                    mask = self._unpack_mask(raw)

            for attr_id, value in resolved.items():
                shift = self._SHIFT_BY_ID[attr_id]

                mask &= ~(self.ZONE_MASK << shift)
                if value:
                    mask |= self.ZONE_MASK << shift

            new_raw = t.LVBytes(self.PREFIX + mask.to_bytes(3, "little"))

            return await self.endpoint.aqara_fp300_manu.write_attributes(
                {self.RAW_ATTR: new_raw},
                manufacturer=AQARA_MFG_CODE,
                **kwargs,
            )


class FP300LedScheduleCluster(LocalDataCluster):
    """Virtual cluster for LED schedule."""

    cluster_id = 0xFCF1
    ep_attribute = "fp300_led_schedule"

    #  Fallback when cache is empty before first successful read (21:00 to 09:00)
    DEFAULT_SCHEDULE: Final = 0x00090015
    # Raw attr on ManuCluster
    RAW_ATTR: Final = AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id

    class AttributeDefs(BaseAttributeDefs):
        led_off_schedule_start_hour: Final = ZCLAttributeDef(
            id=0x0000,
            type=t.uint8_t,
            manufacturer_code=AQARA_MFG_CODE,
        )
        led_off_schedule_end_hour: Final = ZCLAttributeDef(
            id=0x0001,
            type=t.uint8_t,
            manufacturer_code=AQARA_MFG_CODE,
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent overlapping writes
        self._write_mutex = asyncio.Lock()

    def apply_raw(self, raw: int) -> None:
        start = raw & 0xFF
        end = (raw >> 16) & 0xFF

        self._update_attribute(self.AttributeDefs.led_off_schedule_start_hour.id, start)
        self._update_attribute(self.AttributeDefs.led_off_schedule_end_hour.id, end)

    async def write_attributes(
        self,
        attributes: dict[str | int | foundation.ZCLAttributeDef, Any],
        manufacturer: int | UndefinedType | None = UNDEFINED,
        **kwargs,
    ) -> list[list[foundation.WriteAttributesStatusRecord]]:
        async with self._write_mutex:
            manu = self.endpoint.aqara_fp300_manu

            current = manu.get(self.RAW_ATTR)
            if current is None:
                current = self.DEFAULT_SCHEDULE
            start = current & 0xFF
            end = (current >> 16) & 0xFF

            for attr, value in attributes.items():
                attr_id = self.find_attribute(attr).id
                if attr_id == self.AttributeDefs.led_off_schedule_start_hour.id:
                    start = int(value)
                elif attr_id == self.AttributeDefs.led_off_schedule_end_hour.id:
                    end = int(value)

            new_raw = start | (end << 16)

            return await manu.write_attributes(
                {self.RAW_ATTR: new_raw},
                manufacturer=AQARA_MFG_CODE,
                **kwargs,
            )


(
    QuirkBuilder("Aqara", "lumi.sensor_occupy.agl8")
    .friendly_name(manufacturer="Aqara", model="Presence Multi-Sensor FP300")
    .replaces(AqaraFP300ManuCluster)
    .replaces(FP300PowerConfiguration)
    .adds(FP300DetectionRangeCluster)
    .adds(FP300LedScheduleCluster)
    # Presence / PIR
    .binary_sensor(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.presence.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        entity_type=EntityType.STANDARD,
        reporting_config=ReportingConfig(
            min_interval=0,
            max_interval=900,
            reportable_change=1,
        ),
        translation_key="occupancy",
        fallback_name="Occupancy",
    )
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.presence_detection_mode.name,
        enum_class=PresenceDetectionMode,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="presence_detection_mode",
        fallback_name="Presence detection mode",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.absence_delay.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=10,
        max_value=300,
        step=5,
        unit=UnitOfTime.SECONDS,
        translation_key="absence_delay",
        fallback_name="Absence delay",
    )
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.presence_sensitivity.name,
        enum_class=PresenceSensitivity,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="presence_sensitivity",
        fallback_name="Presence sensitivity",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.pir_detection_interval.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=2,
        max_value=300,
        step=1,
        unit=UnitOfTime.SECONDS,
        translation_key="pir_detection_interval",
        fallback_name="PIR detection interval",
    )
    # AI
    .switch(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.ai_interference_identification.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="ai_interference_identification",
        fallback_name="AI interference identification",
    )
    .switch(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.ai_sensitivity_adaptive.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="ai_sensitivity_adaptive",
        fallback_name="AI adaptive sensitivity",
    )
    # Illuminance
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.light_reporting_threshold.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        min_value=3.0,
        max_value=20.0,
        step=0.5,
        multiplier=0.01,
        unit=PERCENTAGE,
        initially_disabled=True,
        translation_key="light_reporting_threshold",
        fallback_name="Light reporting threshold",
    )
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.light_sampling.name,
        enum_class=SamplingFrequency,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="light_sampling",
        fallback_name="Light sampling",
    )
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.light_reporting_mode.name,
        enum_class=ReportMode,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        initially_disabled=True,
        translation_key="light_reporting_mode",
        fallback_name="Light reporting mode",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.light_sampling_period.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=0.5,
        max_value=3600.0,
        step=0.5,
        multiplier=0.001,
        unit=UnitOfTime.SECONDS,
        initially_disabled=True,
        translation_key="light_sampling_period",
        fallback_name="Light sampling period",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.light_reporting_interval.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=600,
        max_value=3600,
        step=600,
        multiplier=0.001,
        unit=UnitOfTime.SECONDS,
        initially_disabled=True,
        translation_key="light_reporting_interval",
        fallback_name="Light reporting interval",
    )
    # Temperature / humidity
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.humidity_reporting_mode.name,
        enum_class=ReportMode,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        initially_disabled=True,
        translation_key="humidity_reporting_mode",
        fallback_name="Humidity reporting mode",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.temp_reporting_threshold.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.TEMPERATURE,
        entity_type=EntityType.CONFIG,
        min_value=0.2,
        max_value=3.0,
        step=0.1,
        multiplier=0.01,
        unit=UnitOfTemperature.CELSIUS,
        initially_disabled=True,
        translation_key="temp_reporting_threshold",
        fallback_name="Temperature reporting threshold",
    )
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.temp_humidity_sampling.name,
        enum_class=SamplingFrequency,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="temp_humidity_sampling",
        fallback_name="Temperature and humidity sampling",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.humidity_reporting_interval.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=600,
        max_value=3600,
        step=600,
        multiplier=0.001,
        unit=UnitOfTime.SECONDS,
        initially_disabled=True,
        translation_key="humidity_reporting_interval",
        fallback_name="Humidity reporting interval",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.temp_humidity_sampling_period.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=0.5,
        max_value=3600.0,
        step=0.5,
        multiplier=0.001,
        unit=UnitOfTime.SECONDS,
        initially_disabled=True,
        translation_key="temp_humidity_sampling_period",
        fallback_name="Temperature and humidity sampling period",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.temp_reporting_interval.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.DURATION,
        entity_type=EntityType.CONFIG,
        min_value=600,
        max_value=3600,
        step=600,
        multiplier=0.001,
        unit=UnitOfTime.SECONDS,
        initially_disabled=True,
        translation_key="temp_reporting_interval",
        fallback_name="Temperature reporting interval",
    )
    .number(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.humidity_reporting_threshold.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=NumberDeviceClass.HUMIDITY,
        entity_type=EntityType.CONFIG,
        min_value=2.0,
        max_value=15.0,
        step=0.5,
        multiplier=0.01,
        unit=PERCENTAGE,
        initially_disabled=True,
        translation_key="humidity_reporting_threshold",
        fallback_name="Humidity reporting threshold",
    )
    .enum(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.temp_reporting_mode.name,
        enum_class=ReportMode,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        initially_disabled=True,
        translation_key="temp_reporting_mode",
        fallback_name="Temperature reporting mode",
    )
    # LED
    .number(
        attribute_name=FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.name,
        cluster_id=FP300LedScheduleCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        min_value=0,
        max_value=23,
        step=1,
        mode="box",
        initially_disabled=True,
        translation_key="led_off_schedule_start_hour",
        fallback_name="LED off schedule start hour",
    )
    .number(
        attribute_name=FP300LedScheduleCluster.AttributeDefs.led_off_schedule_end_hour.name,
        cluster_id=FP300LedScheduleCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        min_value=0,
        max_value=23,
        step=1,
        mode="box",
        initially_disabled=True,
        translation_key="led_off_schedule_end_hour",
        fallback_name="LED off schedule end hour",
    )
    .switch(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.led_off_schedule.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        initially_disabled=True,
        translation_key="led_off_schedule",
        fallback_name="LED off schedule",
    )
    # Buttons
    .write_attr_button(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.spatial_learning.name,
        attribute_value=1,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="spatial_learning",
        fallback_name="Spatial learning",
    )
    .write_attr_button(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.restart_device.name,
        attribute_value=1,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        initially_disabled=True,
        translation_key="restart_device",
        fallback_name="Restart device",
    )
    # Diagnostic
    .sensor(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.target_distance.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfLength.METERS,
        multiplier=0.01,
        entity_type=EntityType.DIAGNOSTIC,
        translation_key="target_distance",
        fallback_name="Target distance",
    )
    .write_attr_button(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.track_target_distance.name,
        attribute_value=1,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        entity_type=EntityType.DIAGNOSTIC,
        translation_key="track_target_distance",
        fallback_name="Track target distance",
    )
    .binary_sensor(
        attribute_name=AqaraFP300ManuCluster.AttributeDefs.pir_detection.name,
        cluster_id=AqaraFP300ManuCluster.cluster_id,
        device_class=BinarySensorDeviceClass.MOTION,
        reporting_config=ReportingConfig(
            min_interval=0,
            max_interval=900,
            reportable_change=1,
        ),
        entity_type=EntityType.DIAGNOSTIC,
        initially_disabled=True,
        translation_key="pir_detection",
        fallback_name="PIR detection",
    )
    .sensor(
        attribute_name="battery_voltage",
        cluster_id=FP300PowerConfiguration.cluster_id,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfElectricPotential.VOLT,
        entity_type=EntityType.DIAGNOSTIC,
        initially_disabled=True,
        translation_key="battery_voltage",
        fallback_name="Battery voltage",
    )
    # Detection range
    .switch(
        attribute_name=FP300DetectionRangeCluster.AttributeDefs.range_0_1m.name,
        cluster_id=FP300DetectionRangeCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="range_0_1m",
        fallback_name="Detection range 0–1 m",
    )
    .switch(
        attribute_name=FP300DetectionRangeCluster.AttributeDefs.range_1_2m.name,
        cluster_id=FP300DetectionRangeCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="range_1_2m",
        fallback_name="Detection range 1–2 m",
    )
    .switch(
        attribute_name=FP300DetectionRangeCluster.AttributeDefs.range_2_3m.name,
        cluster_id=FP300DetectionRangeCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="range_2_3m",
        fallback_name="Detection range 2–3 m",
    )
    .switch(
        attribute_name=FP300DetectionRangeCluster.AttributeDefs.range_3_4m.name,
        cluster_id=FP300DetectionRangeCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="range_3_4m",
        fallback_name="Detection range 3–4 m",
    )
    .switch(
        attribute_name=FP300DetectionRangeCluster.AttributeDefs.range_4_5m.name,
        cluster_id=FP300DetectionRangeCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="range_4_5m",
        fallback_name="Detection range 4–5 m",
    )
    .switch(
        attribute_name=FP300DetectionRangeCluster.AttributeDefs.range_5_6m.name,
        cluster_id=FP300DetectionRangeCluster.cluster_id,
        entity_type=EntityType.CONFIG,
        translation_key="range_5_6m",
        fallback_name="Detection range 5–6 m",
    )
    .add_to_registry()
)
