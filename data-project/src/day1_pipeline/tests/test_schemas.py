"""
파일명: test_schemas.py
작성자: 전우진 P267
작성일: 2026-08-06
설명: pytest를 활용하여 Pydantic 스키마가 
      정상 및 예외 데이터에 대해 의도대로 검증을 수행하는지 확인하는 단위 테스트 모듈입니다.
"""

import pytest
from pydantic import ValidationError

from schemas import IpRecord, WeatherRecord


# 올바른 날씨 데이터가 주어졌을 때 정상적으로 객체가 생성되는지 검증합니다.
def test_weather_record_valid():
    # given
    valid_data = {
        "time": "2026-08-06T12:00",
        "temperature": 25.5,
        "precip_prob": 30
    }
    
    # when
    record = WeatherRecord(**valid_data)
    
    # then
    assert record.temperature == 25.5
    assert record.precip_prob == 30

# 기온이 허용 범위(-50~60)를 초과했을 때 ValidationError를 뱉는지 검증합니다.
def test_weather_record_invalid_temperature():
    # given
    invalid_data = {
        "time": "2026-08-06T12:00",
        "temperature": 100.0, # 범위를 벗어난 온도
        "precip_prob": 30
    }
    
    # when & then
    # pytest.raises를 사용해 ValidationError가 터져야 테스트가 성공하도록 합니다.
    with pytest.raises(ValidationError):
        WeatherRecord(**invalid_data)

# 외부 API의 'query' 키값이 'ip' 필드로 매핑되는지 검증합니다.
def test_ip_record_alias_mapping():
    # given
    raw_api_response = {
        "query": "8.8.8.8",
        "city": "Seoul",
        "lat": 37.5,
        "lon": 127.0
    }
    
    # when
    record = IpRecord(**raw_api_response)
    
    # then
    assert record.ip == "8.8.8.8"