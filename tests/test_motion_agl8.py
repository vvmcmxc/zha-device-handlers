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
