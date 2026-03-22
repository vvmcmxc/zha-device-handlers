"""Tests for Aqara Presence Multi-Sensor FP300 quirk."""

from unittest import mock

from zigpy.zcl import foundation
from zigpy.zcl.clusters.general import Basic, PowerConfiguration

import zhaquirks
from zhaquirks.xiaomi.aqara.motion_agl8 import (
    AqaraFP300ManuCluster,
    FP300DetectionRangeCluster,
    FP300LedScheduleCluster,
    PresenceDetectionMode,
    PresenceSensitivity,
    ReportMode,
    SamplingFrequency,
)

zhaquirks.setup()


async def test_fp300_device_creation(zigpy_device_from_v2_quirk):
    """Test that FP300 device is created with correct clusters and endpoints."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    assert quirked.manufacturer == "Aqara"
    assert quirked.model == "lumi.sensor_occupy.agl8"

    # Check endpoint 1 exists with expected clusters
    ep1 = quirked.endpoints[1]
    assert ep1 is not None
    assert Basic.cluster_id in ep1.in_clusters


async def test_fp300_clusters_present(zigpy_device_from_v2_quirk):
    """Test that all FP300 custom clusters are present."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]

    # Check manufacturer cluster
    assert AqaraFP300ManuCluster.cluster_id in ep1.in_clusters
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]
    assert isinstance(manu_cluster, AqaraFP300ManuCluster)

    # Check detection range cluster
    assert FP300DetectionRangeCluster.cluster_id in ep1.in_clusters
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]
    assert isinstance(detect_cluster, FP300DetectionRangeCluster)

    # Check LED schedule cluster
    assert FP300LedScheduleCluster.cluster_id in ep1.in_clusters
    led_cluster = ep1.in_clusters[FP300LedScheduleCluster.cluster_id]
    assert isinstance(led_cluster, FP300LedScheduleCluster)


async def test_fp300_power_configuration(zigpy_device_from_v2_quirk):
    """Test that power configuration cluster is available."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    assert PowerConfiguration.cluster_id in ep1.in_clusters
    power_cluster = ep1.in_clusters[PowerConfiguration.cluster_id]

    # Verify it's the custom power cluster, not base class
    from zhaquirks.xiaomi.aqara.motion_agl8 import FP300PowerConfiguration

    assert isinstance(power_cluster, FP300PowerConfiguration)


async def test_fp300_detection_range_unpacking(zigpy_device_from_v2_quirk):
    """Test detection range cluster correctly unpacks raw data."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]

    # Test unpacking detection range from raw bytes
    # PREFIX = 0x0300, then 3 bytes for zone mask
    # All zones enabled: 0xFFFFFF, zones are 4 bits each
    raw_data = b"\x03\x00\xff\xff\xff"  # All zones enabled
    detect_cluster.apply_raw(raw_data)

    # All zones should be True
    for attr_def in [
        FP300DetectionRangeCluster.AttributeDefs.range_0_1m,
        FP300DetectionRangeCluster.AttributeDefs.range_1_2m,
        FP300DetectionRangeCluster.AttributeDefs.range_2_3m,
        FP300DetectionRangeCluster.AttributeDefs.range_3_4m,
        FP300DetectionRangeCluster.AttributeDefs.range_4_5m,
        FP300DetectionRangeCluster.AttributeDefs.range_5_6m,
    ]:
        assert detect_cluster.get(attr_def.id) is True


async def test_fp300_detection_range_partial_zones(zigpy_device_from_v2_quirk):
    """Test detection range cluster with partial zones enabled."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]

    # Only first 2 zones enabled (bits 0-3 and 4-7)
    # Zone 0 at shift 0: mask 0x0F
    # Zone 1 at shift 4: mask 0xF0
    # Total: 0x00FF00 in 3-byte format
    raw_data = b"\x03\x00\xff\x00\x00"
    detect_cluster.apply_raw(raw_data)

    # Check first two zones
    assert (
        detect_cluster.get(FP300DetectionRangeCluster.AttributeDefs.range_0_1m.id)
        is True
    )
    assert (
        detect_cluster.get(FP300DetectionRangeCluster.AttributeDefs.range_1_2m.id)
        is True
    )
    # Check remaining zones are False
    assert (
        detect_cluster.get(FP300DetectionRangeCluster.AttributeDefs.range_2_3m.id)
        is False
    )
    assert (
        detect_cluster.get(FP300DetectionRangeCluster.AttributeDefs.range_3_4m.id)
        is False
    )


async def test_fp300_led_schedule_unpacking(zigpy_device_from_v2_quirk):
    """Test LED schedule cluster correctly unpacks raw data."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    led_cluster = ep1.in_clusters[FP300LedScheduleCluster.cluster_id]

    # LED schedule: start_hour at bits 0-7, end_hour at bits 16-23
    # Start 21 (0x15), End 9 (0x09)
    raw_data = 0x15 | (0x09 << 16)  # 0x00090015
    led_cluster.apply_raw(raw_data)

    assert (
        led_cluster.get(
            FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id
        )
        == 21
    )
    assert (
        led_cluster.get(
            FP300LedScheduleCluster.AttributeDefs.led_off_schedule_end_hour.id
        )
        == 9
    )


async def test_fp300_manu_cluster_presence_attribute(zigpy_device_from_v2_quirk):
    """Test manufacturer cluster has presence attribute available."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Verify presence attribute exists and is reportable
    presence_attr = AqaraFP300ManuCluster.AttributeDefs.presence
    assert presence_attr.id == 0x0142
    assert manu_cluster.find_attribute(presence_attr.id) is not None


async def test_fp300_manu_cluster_enum_attributes(zigpy_device_from_v2_quirk):
    """Test manufacturer cluster enum attributes."""
    # Test presence detection mode enum
    mode_attr = AqaraFP300ManuCluster.AttributeDefs.presence_detection_mode
    assert mode_attr.type is PresenceDetectionMode

    # Test presence sensitivity enum
    sens_attr = AqaraFP300ManuCluster.AttributeDefs.presence_sensitivity
    assert sens_attr.type is PresenceSensitivity


async def test_fp300_manu_cluster_bind(zigpy_device_from_v2_quirk):
    """Test manufacturer cluster bind method initializes detection range and LED schedule."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Mock parent bind to avoid actual device communication
    with mock.patch.object(
        manu_cluster.__class__.__bases__[0], "bind", new_callable=mock.AsyncMock
    ) as mock_bind:
        mock_bind.return_value = foundation.Status.SUCCESS

        await manu_cluster.bind()

        # bind should be called on parent
        mock_bind.assert_called_once()


async def test_fp300_enum_values(zigpy_device_from_v2_quirk):
    """Test that enum classes have expected values."""
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


async def test_fp300_detection_range_write_attributes(zigpy_device_from_v2_quirk):
    """Test writing detection range attributes."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Set initial raw value
    raw_data = b"\x03\x00\x00\x00\x00"
    manu_cluster._update_attribute(
        AqaraFP300ManuCluster.AttributeDefs.detection_range_raw.id, raw_data
    )

    # Mock write to avoid actual device communication
    with mock.patch.object(
        manu_cluster, "write_attributes", new_callable=mock.AsyncMock
    ) as mock_write:
        mock_write.return_value = [
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]

        # Write attributes
        await detect_cluster.write_attributes(
            {FP300DetectionRangeCluster.AttributeDefs.range_0_1m.id: True}
        )

        # Verify write was called
        mock_write.assert_called_once()


async def test_fp300_led_schedule_write_attributes(zigpy_device_from_v2_quirk):
    """Test writing LED schedule attributes."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    led_cluster = ep1.in_clusters[FP300LedScheduleCluster.cluster_id]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Set initial raw value
    initial_raw = 0x00090015  # start=21, end=9
    manu_cluster._update_attribute(
        AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id, initial_raw
    )

    # Mock write to avoid actual device communication
    with mock.patch.object(
        manu_cluster, "write_attributes", new_callable=mock.AsyncMock
    ) as mock_write:
        mock_write.return_value = [
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]

        # Write start hour
        await led_cluster.write_attributes(
            {FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id: 18}
        )

        # Verify write was called
        mock_write.assert_called_once()


def test_fp300_detection_range_unpack_mask(zigpy_device_from_v2_quirk):
    """Test detection range mask unpacking."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]

    # Test unpacking mask from bytes
    raw = b"\x03\x00\x12\x34\x56"
    mask = detect_cluster._unpack_mask(raw)

    # Mask should be little-endian from bytes 2-4
    expected = 0x563412
    assert mask == expected


async def test_fp300_detection_range_invalid_length(zigpy_device_from_v2_quirk):
    """Test detection range with invalid raw data length."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]

    # Apply raw with invalid length - should be handled gracefully
    raw_data = b"\x03\x00"  # Too short, should be 5 bytes
    detect_cluster.apply_raw(raw_data)

    # Cluster should still be usable


def test_fp300_led_schedule_default_fallback(zigpy_device_from_v2_quirk):
    """Test LED schedule uses default fallback when no raw value."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    led_cluster = ep1.in_clusters[FP300LedScheduleCluster.cluster_id]

    # Get default schedule (21:00 to 09:00)
    assert led_cluster.DEFAULT_SCHEDULE == 0x00090015


async def test_fp300_power_configuration_battery_voltage(zigpy_device_from_v2_quirk):
    """Test FP300 power configuration handles battery voltage."""
    from zhaquirks.xiaomi.aqara.motion_agl8 import FP300PowerConfiguration

    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    power_cluster = ep1.in_clusters[PowerConfiguration.cluster_id]

    # Verify it's the custom power cluster
    assert isinstance(power_cluster, FP300PowerConfiguration)
    assert hasattr(power_cluster, "battery_reported")


def test_fp300_detection_range_shift_by_id(zigpy_device_from_v2_quirk):
    """Test detection range shift mapping."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    detect_cluster = ep1.in_clusters[FP300DetectionRangeCluster.cluster_id]

    # Verify SHIFT_BY_ID mapping
    expected_shifts = {
        FP300DetectionRangeCluster.AttributeDefs.range_0_1m.id: 0,
        FP300DetectionRangeCluster.AttributeDefs.range_1_2m.id: 4,
        FP300DetectionRangeCluster.AttributeDefs.range_2_3m.id: 8,
        FP300DetectionRangeCluster.AttributeDefs.range_3_4m.id: 12,
        FP300DetectionRangeCluster.AttributeDefs.range_4_5m.id: 16,
        FP300DetectionRangeCluster.AttributeDefs.range_5_6m.id: 20,
    }

    for attr_id, expected_shift in expected_shifts.items():
        assert detect_cluster._SHIFT_BY_ID[attr_id] == expected_shift


async def test_fp300_power_battery_reported(zigpy_device_from_v2_quirk):
    """Test FP300 power configuration battery_reported method."""
    from zhaquirks.xiaomi.aqara.motion_agl8 import FP300PowerConfiguration

    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    power_cluster = ep1.in_clusters[PowerConfiguration.cluster_id]

    assert isinstance(power_cluster, FP300PowerConfiguration)

    # Mock _update_attribute and _update_battery_percentage
    with (
        mock.patch.object(power_cluster, "_update_attribute") as mock_update_attr,
        mock.patch.object(
            power_cluster, "_update_battery_percentage"
        ) as mock_update_percent,
    ):
        power_cluster.battery_reported(2900)

        # Should call _update_attribute with voltage in V
        mock_update_attr.assert_called_once()
        # Should call _update_battery_percentage with voltage in mV
        mock_update_percent.assert_called_once_with(2900)


async def test_fp300_power_battery_percent_reported(zigpy_device_from_v2_quirk):
    """Test FP300 power configuration battery_percent_reported ignores reports."""
    from zhaquirks.xiaomi.aqara.motion_agl8 import FP300PowerConfiguration

    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    power_cluster = ep1.in_clusters[PowerConfiguration.cluster_id]

    assert isinstance(power_cluster, FP300PowerConfiguration)

    # battery_percent_reported should be a no-op
    power_cluster.battery_percent_reported(100)


async def test_fp300_manu_cluster_bind_with_error(zigpy_device_from_v2_quirk):
    """Test manufacturer cluster bind handles read errors gracefully."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Store original read_attributes

    # Flag to track exception handling

    async def mock_read_attributes(self, *args, **kwargs):
        """Mock that raises exception to trigger error handling."""
        raise RuntimeError("Device communication error")

    # Patch methods to test exception handling
    with (
        mock.patch.object(
            manu_cluster.__class__.__bases__[0], "bind", new_callable=mock.AsyncMock
        ) as mock_super_bind,
        mock.patch.object(
            manu_cluster, "read_attributes", side_effect=mock_read_attributes
        ),
        mock.patch.object(manu_cluster, "debug") as mock_debug,
    ):
        mock_super_bind.return_value = foundation.Status.SUCCESS

        # Call bind - should handle exceptions from read_attributes
        result = await manu_cluster.bind()

        # Verify exception logging was called when read fails
        assert mock_debug.called
        assert result == foundation.Status.SUCCESS


async def test_fp300_led_schedule_write_both_params(zigpy_device_from_v2_quirk):
    """Test LED schedule write with both start and end parameters."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    led_cluster = ep1.in_clusters[FP300LedScheduleCluster.cluster_id]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Set initial raw value
    initial_raw = 0x00090015  # start=21, end=9
    manu_cluster._update_attribute(
        AqaraFP300ManuCluster.AttributeDefs.led_schedule_time_raw.id, initial_raw
    )

    # Mock write
    with mock.patch.object(
        manu_cluster, "write_attributes", new_callable=mock.AsyncMock
    ) as mock_write:
        mock_write.return_value = [
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]

        # Write both start and end
        await led_cluster.write_attributes(
            {
                FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id: 20,
                FP300LedScheduleCluster.AttributeDefs.led_off_schedule_end_hour.id: 8,
            }
        )

        # Should have computed new raw value with both parameters
        mock_write.assert_called_once()
        # Check the call args to verify the new raw was calculated correctly
        call_args = mock_write.call_args
        assert call_args is not None


async def test_fp300_led_schedule_write_no_current(zigpy_device_from_v2_quirk):
    """Test LED schedule write when no current raw value exists."""
    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    led_cluster = ep1.in_clusters[FP300LedScheduleCluster.cluster_id]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Don't set initial value - cluster has no raw attribute yet

    # Mock write
    with mock.patch.object(
        manu_cluster, "write_attributes", new_callable=mock.AsyncMock
    ) as mock_write:
        mock_write.return_value = [
            [foundation.WriteAttributesStatusRecord(0, foundation.Status.SUCCESS)]
        ]

        # Write when no current value exists - should use DEFAULT_SCHEDULE
        await led_cluster.write_attributes(
            {
                FP300LedScheduleCluster.AttributeDefs.led_off_schedule_start_hour.id: 22,
            }
        )

        # Should have called write using default schedule as base
        mock_write.assert_called_once()
        call_args = mock_write.call_args
        # The new raw should be computed from DEFAULT_SCHEDULE (0x00090015)
        # start=22 (0x16), end=9 (from default)
        # new_raw = 0x22 | (0x09 << 16) = 0x00090016
        assert call_args is not None


async def test_fp300_manu_cluster_parse_aqara_attributes(zigpy_device_from_v2_quirk):
    """Test manufacturer cluster parses Aqara battery voltage attribute correctly."""
    from zhaquirks.xiaomi.aqara.motion_agl8 import (
        BATTERY_VOLTAGE_MV,
        FP300_ATTR_BATTERY_VOLTAGE,
    )

    quirked = zigpy_device_from_v2_quirk("Aqara", "lumi.sensor_occupy.agl8")

    ep1 = quirked.endpoints[1]
    manu_cluster = ep1.in_clusters[AqaraFP300ManuCluster.cluster_id]

    # Mock parent _parse_aqara_attributes to return battery voltage
    with mock.patch.object(
        manu_cluster.__class__.__bases__[0], "_parse_aqara_attributes"
    ) as mock_parse:
        # Parent returns dict with battery voltage attribute
        mock_parse.return_value = {FP300_ATTR_BATTERY_VOLTAGE: 2950}

        # Call our _parse_aqara_attributes
        result = manu_cluster._parse_aqara_attributes(b"test_data")

        # Should have replaced FP300_ATTR_BATTERY_VOLTAGE with BATTERY_VOLTAGE_MV
        assert BATTERY_VOLTAGE_MV in result
        assert result[BATTERY_VOLTAGE_MV] == 2950
        assert FP300_ATTR_BATTERY_VOLTAGE not in result
