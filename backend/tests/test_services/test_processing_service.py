"""
数据处理服务测试
"""
import pytest
import numpy as np
from PIL import Image
from app.services.processing_service import CoordinateMapper, ColorScaleParser


class TestCoordinateMapper:
    """坐标映射器测试"""

    def test_geo_to_pixel_conversion(self):
        """测试经纬度到像素坐标转换"""
        mapper = CoordinateMapper(width=1000, height=1000)

        # 测试中心点
        pixel_x, pixel_y = mapper.geo_to_pixel(105.0, 35.0)
        assert pixel_x == 500
        assert pixel_y == 500

        # 测试边界点
        pixel_x, pixel_y = mapper.geo_to_pixel(105.35, 35.35)
        assert pixel_x == 999  # 接近右边界
        assert pixel_y == 999  # 接近下边界

    def test_pixel_to_geo_conversion(self):
        """测试像素坐标到经纬度转换"""
        mapper = CoordinateMapper(width=1000, height=1000)

        # 测试中心点
        lon, lat = mapper.pixel_to_geo(500, 500)
        assert abs(lon - 105.0) < 0.01
        assert abs(lat - 35.0) < 0.01

    def test_round_trip_conversion(self):
        """测试往返转换的一致性"""
        mapper = CoordinateMapper(width=1000, height=1000)

        # 原始坐标
        original_lon, original_lat = 116.4, 39.9

        # 转换为像素再转回
        pixel_x, pixel_y = mapper.geo_to_pixel(original_lon, original_lat)
        result_lon, result_lat = mapper.pixel_to_geo(pixel_x, pixel_y)

        # 验证误差在可接受范围内
        assert abs(original_lon - result_lon) < 0.01
        assert abs(original_lat - result_lat) < 0.01


class TestColorScaleParser:
    """颜色标尺解析器测试"""

    def test_rgb_to_dbz_conversion_no_echo(self):
        """测试无回波区域的RGB到dBZ转换"""
        parser = ColorScaleParser()

        # 黑色 (无回波)
        dbz = parser.rgb_to_dbz(0, 0, 0)
        assert 0 <= dbz <= 5

    def test_rgb_to_dbz_conversion_weak(self):
        """测试弱回波的RGB到dBZ转换"""
        parser = ColorScaleParser()

        # 绿色 (弱回波)
        dbz = parser.rgb_to_dbz(0, 255, 0)
        assert 10 <= dbz <= 15

    def test_rgb_to_dbz_conversion_moderate(self):
        """测试中等回波的RGB到dBZ转换"""
        parser = ColorScaleParser()

        # 黄色 (中等回波)
        dbz = parser.rgb_to_dbz(255, 255, 0)
        assert 20 <= dbz <= 25

    def test_rgb_to_dbz_conversion_heavy(self):
        """测试强回波的RGB到dBZ转换"""
        parser = ColorScaleParser()

        # 红色 (强回波)
        dbz = parser.rgb_to_dbz(255, 0, 0)
        assert 45 <= dbz <= 50

    def test_cloud_impact_factor_calculation(self):
        """测试云影响因子计算"""
        parser = ColorScaleParser()

        # 无回波 (影响因子低)
        factor_low = parser.get_cloud_impact_factor(5)
        assert 0 <= factor_low <= 0.2

        # 中等回波 (影响因子中等)
        factor_medium = parser.get_cloud_impact_factor(30)
        assert 0.4 <= factor_medium <= 0.6

        # 强回波 (影响因子高)
        factor_high = parser.get_cloud_impact_factor(60)
        assert factor_high >= 0.8

    def test_get_dbz_category(self):
        """测试dBZ等级分类"""
        parser = ColorScaleParser()

        assert parser.get_dbz_category(5) == "no_echo"
        assert parser.get_dbz_category(15) == "weak"
        assert parser.get_dbz_category(25) == "moderate"
        assert parser.get_dbz_category(35) == "strong"
        assert parser.get_dbz_category(55) == "severe"
        assert parser.get_dbz_category(70) == "maximum"
