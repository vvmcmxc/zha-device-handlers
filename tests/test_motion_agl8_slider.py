"""Tests for Aqara Presence Multi-Sensor FP300 slider quirk."""

from types import SimpleNamespace
from unittest import mock

from zigpy.zcl import foundation

import zhaquirks
from zhaquirks.xiaomi import BATTERY_VOLTAGE_MV, XiaomiAqaraE1Cluster
from zhaquirks.xiaomi.aqara.motion_agl8_slider import (
    AQARA_MFG_CODE,
    FP300_ATTR_BATTERY_PERCENT,
    FP300_ATTR_BATTERY_VOLTAGE,
    AqaraFP300ManuCluster,
    FP300DetectionSliderCluster,
    FP300LedScheduleCluster,
    FP300PowerConfiguration,
    PresenceDetectionMode,
    PresenceSensitivity,
    ReportMode,
    SamplingFrequency,
)

zhaquirks.setup()


def test_fp300_detection_slider_apply_raw():
    """Detection slider should convert bitmask to number of enabled steps."""
    slider = FP300DetectionSliderCluster.__new__(FP300DetectionSliderCluster)
    slider._update_attribute = mock.Mock()
    slider.debug = mock.Mock()

    FP300DetectionSliderCluster.apply_raw(slider, b"\x00\x03\x3f\x00\x00")

    slider._update_attribute.assert_called_once_with(
        FP300DetectionSliderCluster.AttributeDefs.max_distance_steps.id,
        6,
    )


def test_fp300_detection_slider_invalid_raw():
    """Detection slider should ignore invalid payload lengths."""
    slider = FP300DetectionSliderCluster.__new__(FP300DetectionSliderCluster)
    slider._update_attribute = mock.Mock()
    slider.debug = mock.Mock()

    FP300DetectionSliderCluster.apply_raw(slider, b"\x00\x03")

    slider._update_attribute.assert_not_called()
    slider.debug.assert_called_once()


def test_fp300_detection_slider_apply_raw_zero_mask():
    """Zero detection mask should produce zero steps."""
    slider = FP300DetectionSliderCluster.__new__(FP300DetectionSliderCluster)
    slider._update_attribute = mock.Mock()
    slider.debug = mock.Mock()

    FP300DetectionSliderCluster.apply_raw(slider, b"\x00\x03\x00\x00\x00")

    slider._update_attribute.assert_called_once_with(
        FP300DetectionSliderCluster.AttributeDefs.max_distance_steps.id,
        0,
    )


async def test_fp300_detection_slider_write_attributes():
    """Detection slider writes a packed mask into manufacturer attribute."""
    write_mock = mock.AsyncMock(
        return_value=[
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]
    )
    slider = FP300DetectionSliderCluster.__new__(FP300DetectionSliderCluster)
    slider._endpoint = SimpleNamespace(
        aqara_fp300_manu=SimpleNamespace(write_attributes=write_mock)
    )
    slider.find_attribute = lambda attr: SimpleNamespace(id=int(attr))

    await FP300DetectionSliderCluster.write_attributes(
        slider,
        {FP300DetectionSliderCluster.AttributeDefs.max_distance_steps.id: 4},
    )

    expected_raw = b"\x00\x03\x0f\x00\x00"
    write_mock.assert_called_once_with(
        {AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id: expected_raw},
        manufacturer=AQARA_MFG_CODE,
    )


async def test_fp300_detection_slider_write_attributes_clamps_high():
    """Detection slider should clamp writes above 24 steps."""
    write_mock = mock.AsyncMock(
        return_value=[
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]
    )
    slider = FP300DetectionSliderCluster.__new__(FP300DetectionSliderCluster)
    slider._endpoint = SimpleNamespace(
        aqara_fp300_manu=SimpleNamespace(write_attributes=write_mock)
    )
    slider.find_attribute = lambda attr: SimpleNamespace(id=int(attr))

    await FP300DetectionSliderCluster.write_attributes(
        slider,
        {FP300DetectionSliderCluster.AttributeDefs.max_distance_steps.id: 99},
    )

    expected_raw = b"\x00\x03\xff\xff\xff"
    write_mock.assert_called_once_with(
        {AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id: expected_raw},
        manufacturer=AQARA_MFG_CODE,
    )


async def test_fp300_detection_slider_write_attributes_clamps_low():
    """Detection slider should clamp writes below zero."""
    write_mock = mock.AsyncMock(
        return_value=[
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]
    )
    slider = FP300DetectionSliderCluster.__new__(FP300DetectionSliderCluster)
    slider._endpoint = SimpleNamespace(
        aqara_fp300_manu=SimpleNamespace(write_attributes=write_mock)
    )
    slider.find_attribute = lambda attr: SimpleNamespace(id=int(attr))

    await FP300DetectionSliderCluster.write_attributes(
        slider,
        {FP300DetectionSliderCluster.AttributeDefs.max_distance_steps.id: -2},
    )

    expected_raw = b"\x00\x03\x00\x00\x00"
    write_mock.assert_called_once_with(
        {AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id: expected_raw},
        manufacturer=AQARA_MFG_CODE,
    )


def test_fp300_led_schedule_apply_raw():
    """LED schedule raw value should update start and end attributes."""
    led = FP300LedScheduleCluster.__new__(FP300LedScheduleCluster)
    led._update_attribute = mock.Mock()

    FP300LedScheduleCluster.apply_raw(led, 0x00090015)

    led._update_attribute.assert_any_call(
        FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id,
        21,
    )
    led._update_attribute.assert_any_call(
        FP300LedScheduleCluster.AttributeDefs.led_off_schedule_end_hour.id,
        9,
    )


async def test_fp300_led_schedule_write_with_default_fallback():
    """LED schedule writes should use default schedule when cache is empty."""
    write_mock = mock.AsyncMock(
        return_value=[
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]
    )
    manu = SimpleNamespace(get=lambda _attr: None, write_attributes=write_mock)
    led = FP300LedScheduleCluster.__new__(FP300LedScheduleCluster)
    led._endpoint = SimpleNamespace(aqara_fp300_manu=manu)
    led.find_attribute = lambda attr: SimpleNamespace(id=int(attr))

    await FP300LedScheduleCluster.write_attributes(
        led,
        {FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id: 22},
    )

    expected_raw = 0x00090016
    write_mock.assert_called_once_with(
        {AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id: expected_raw},
        manufacturer=AQARA_MFG_CODE,
    )


async def test_fp300_led_schedule_write_preserves_other_side():
    """Updating only one LED boundary should keep the other value intact."""
    write_mock = mock.AsyncMock(
        return_value=[
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]
    )
    manu = SimpleNamespace(get=lambda _attr: 0x00070014, write_attributes=write_mock)
    led = FP300LedScheduleCluster.__new__(FP300LedScheduleCluster)
    led._endpoint = SimpleNamespace(aqara_fp300_manu=manu)
    led.find_attribute = lambda attr: SimpleNamespace(id=int(attr))

    await FP300LedScheduleCluster.write_attributes(
        led,
        {FP300LedScheduleCluster.AttributeDefs.led_off_schedule_end_hour.id: 10},
    )

    expected_raw = 0x000A0014
    write_mock.assert_called_once_with(
        {AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id: expected_raw},
        manufacturer=AQARA_MFG_CODE,
    )


async def test_fp300_led_schedule_write_updates_both_boundaries():
    """When both boundaries are provided both should be encoded."""
    write_mock = mock.AsyncMock(
        return_value=[
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]
    )
    manu = SimpleNamespace(get=lambda _attr: 0x00070014, write_attributes=write_mock)
    led = FP300LedScheduleCluster.__new__(FP300LedScheduleCluster)
    led._endpoint = SimpleNamespace(aqara_fp300_manu=manu)
    led.find_attribute = lambda attr: SimpleNamespace(id=int(attr))

    await FP300LedScheduleCluster.write_attributes(
        led,
        {
            FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id: 23,
            FP300LedScheduleCluster.AttributeDefs.led_off_schedule_end_hour.id: 5,
        },
    )

    expected_raw = 0x00050017
    write_mock.assert_called_once_with(
        {AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id: expected_raw},
        manufacturer=AQARA_MFG_CODE,
    )


def test_fp300_manu_cluster_forwards_raw_updates():
    """Manufacturer cluster should forward raw values to virtual clusters."""
    manu = AqaraFP300ManuCluster.__new__(AqaraFP300ManuCluster)
    slider = SimpleNamespace(apply_raw=mock.Mock())
    led = SimpleNamespace(apply_raw=mock.Mock())
    manu._endpoint = SimpleNamespace(
        fp300_detection_slider=slider,
        fp300_led_schedule=led,
    )

    with mock.patch.object(XiaomiAqaraE1Cluster, "_update_attribute"):
        AqaraFP300ManuCluster._update_attribute(
            manu,
            AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id,
            b"\x00\x03\x01\x00\x00",
        )
        AqaraFP300ManuCluster._update_attribute(
            manu,
            AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id,
            0x00090015,
        )

    slider.apply_raw.assert_called_once()
    led.apply_raw.assert_called_once_with(0x00090015)


def test_fp300_manu_cluster_ignores_unrelated_attr_for_virtuals():
    """Unrelated attribute updates should not call virtual cluster handlers."""
    manu = AqaraFP300ManuCluster.__new__(AqaraFP300ManuCluster)
    slider = SimpleNamespace(apply_raw=mock.Mock())
    led = SimpleNamespace(apply_raw=mock.Mock())
    manu._endpoint = SimpleNamespace(
        fp300_detection_slider=slider,
        fp300_led_schedule=led,
    )

    with mock.patch.object(XiaomiAqaraE1Cluster, "_update_attribute"):
        AqaraFP300ManuCluster._update_attribute(
            manu,
            AqaraFP300ManuCluster.AttributeDefs.presence.id,
            True,
        )

    slider.apply_raw.assert_not_called()
    led.apply_raw.assert_not_called()


def test_fp300_manu_parse_aqara_attributes_maps_battery_voltage():
    """Aqara battery voltage key should be converted to BATTERY_VOLTAGE_MV."""
    manu = AqaraFP300ManuCluster.__new__(AqaraFP300ManuCluster)

    with mock.patch.object(
        XiaomiAqaraE1Cluster,
        "_parse_aqara_attributes",
        return_value={FP300_ATTR_BATTERY_VOLTAGE: 2965},
    ):
        parsed = AqaraFP300ManuCluster._parse_aqara_attributes(manu, b"ignored")

    assert parsed[BATTERY_VOLTAGE_MV] == 2965
    assert FP300_ATTR_BATTERY_VOLTAGE not in parsed


def test_fp300_manu_parse_aqara_attributes_without_battery_voltage():
    """Parser should preserve attributes when no FP300 battery key exists."""
    manu = AqaraFP300ManuCluster.__new__(AqaraFP300ManuCluster)

    with mock.patch.object(
        XiaomiAqaraE1Cluster,
        "_parse_aqara_attributes",
        return_value={"other": 1},
    ):
        parsed = AqaraFP300ManuCluster._parse_aqara_attributes(manu, b"ignored")

    assert parsed == {"other": 1}


async def test_fp300_manu_bind_reads_initial_attrs():
    """Bind should trigger initial reads for detection and LED raw attributes."""
    manu = AqaraFP300ManuCluster.__new__(AqaraFP300ManuCluster)
    manu.read_attributes = mock.AsyncMock(return_value=({}, {}))
    manu.debug = mock.Mock()

    with mock.patch.object(
        XiaomiAqaraE1Cluster,
        "bind",
        new=mock.AsyncMock(return_value=foundation.Status.SUCCESS),
    ) as mock_super_bind:
        result = await AqaraFP300ManuCluster.bind(manu)

    assert result == foundation.Status.SUCCESS
    mock_super_bind.assert_called_once()
    assert manu.read_attributes.await_count == 2
    manu.read_attributes.assert_any_await(
        [AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id],
        allow_cache=False,
        manufacturer=AQARA_MFG_CODE,
    )
    manu.read_attributes.assert_any_await(
        [AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id],
        allow_cache=False,
        manufacturer=AQARA_MFG_CODE,
    )


async def test_fp300_manu_bind_continues_on_read_error():
    """Bind should log and continue when initial attribute reads fail."""
    manu = AqaraFP300ManuCluster.__new__(AqaraFP300ManuCluster)
    manu.read_attributes = mock.AsyncMock(side_effect=RuntimeError("boom"))
    manu.debug = mock.Mock()

    with mock.patch.object(
        XiaomiAqaraE1Cluster,
        "bind",
        new=mock.AsyncMock(return_value=foundation.Status.SUCCESS),
    ):
        result = await AqaraFP300ManuCluster.bind(manu)

    assert result == foundation.Status.SUCCESS
    assert manu.read_attributes.await_count == 2
    assert manu.debug.call_count == 2


def test_fp300_power_cluster_battery_reporting():
    """Power cluster should map mV reports and ignore buggy percent reports."""
    power = FP300PowerConfiguration.__new__(FP300PowerConfiguration)

    with (
        mock.patch.object(power, "_update_attribute") as mock_update_attr,
        mock.patch.object(power, "_update_battery_percentage") as mock_update_pct,
    ):
        FP300PowerConfiguration.battery_reported(power, 2900)
        FP300PowerConfiguration.battery_percent_reported(power, 77)

    mock_update_attr.assert_called_once()
    mock_update_pct.assert_called_once_with(2900)


def test_fp300_power_cluster_voltage_limits_constants():
    """Power cluster keeps configured minimum and maximum voltage boundaries."""
    assert FP300PowerConfiguration.MIN_VOLTS_MV == 2800
    assert FP300PowerConfiguration.MAX_VOLTS_MV == 3000


def test_fp300_led_schedule_default_constant():
    """LED schedule fallback default should match documented raw value."""
    assert FP300LedScheduleCluster.DEFAULT_SCHEDULE == 0x00090015


def test_fp300_detection_slider_prefix_constant():
    """Detection slider should use expected Aqara raw payload prefix."""
    assert FP300DetectionSliderCluster.PREFIX == b"\x00\x03"


def test_fp300_enum_values():
    """Enum classes should preserve expected firmware values."""
    assert PresenceSensitivity.Low == 1
    assert PresenceSensitivity.Medium == 2
    assert PresenceSensitivity.High == 3

    assert PresenceDetectionMode.Both == 0
    assert PresenceDetectionMode.Only_mmWave == 1
    assert PresenceDetectionMode.Only_PIR == 2

    assert SamplingFrequency.Off == 0
    assert SamplingFrequency.Low == 1
    assert SamplingFrequency.Medium == 2
    assert SamplingFrequency.High == 3
    assert SamplingFrequency.Custom == 4

    assert ReportMode.Threshold == 1
    assert ReportMode.Interval == 2
    assert ReportMode.Threshold_and_interval == 3


def test_fp300_attribute_key_constants():
    """Known Aqara battery keys should stay stable."""
    assert FP300_ATTR_BATTERY_VOLTAGE == "0xff01-23"
    assert FP300_ATTR_BATTERY_PERCENT == "0xff01-24"
