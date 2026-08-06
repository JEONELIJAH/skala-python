import logging

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

# Pydantic 스키마 정의
class WeatherRecord(BaseModel):
    # Weather API 검증 스키마
    time: str
    temperature: float = Field(ge=-50, le=60)
    precip_prob: int = Field(ge=0, le=100)

class CountryRecord(BaseModel):
    # Country API 검증 스키마
    flag: str
    name: str = Field(min_length=1)
    region: str = Field(min_length=1)
    subregion: str | None = None
    population: int = Field(ge=0)

class IpRecord(BaseModel):
    # IP API 검증 스키마
    ip: str = Field(alias="query")
    city: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    isp: str | None = None


# 데이터 추출 및 검증 파이프라인
def validate_data(raw_data):
    # 수집된 raw 데이터를 Pydantic으로 검증합니다
    print("--- Pydantic 데이터 검증 시작 ---")
    
    validated_results = {
        "ip": None,
        "country": None,
        "weather": []
    }

    # 1) Weather 데이터 검증 (Zip을 활용한 리스트 해체 및 재조립)
    if raw_weather := raw_data.get("weather"):
        hourly_data = raw_weather.get("hourly", {})
        times = hourly_data.get("time", [])
        temps = hourly_data.get("temperature_2m", [])
        probs = hourly_data.get("precipitation_probability", [])
        
        for t, temp, prob in zip(times, temps, probs):
            record_dict = {
                "time": t,
                "temperature": temp,
                "precip_prob": prob
            }
            try:
                # 딕셔너리 언패킹으로 record_dict를 푼 값을 Pydantic 스키마 WeatherRecord에서 검증합니다.
                record = WeatherRecord(**record_dict)
                validated_results["weather"].append(record)
            except ValidationError as e:
                logger.error(f"❌ [Weather] 시간대({t}) 검증 실패:\n{e}")

        print(f"✅ [Weather] 데이터 검증 통과 (총 {len(validated_results['weather'])}건 정상)")

    # 2) Country 데이터 검증
    if raw_country := raw_data.get("country"):
        try:
            # 리스트 응답일 경우 첫 번째 요소 추출
            data_to_validate = raw_country[0] if isinstance(raw_country, list) else raw_country
            # 딕셔너리 언패킹으로 data_to_validate를 푼 값을 Pydantic 스키마 CountryRecord에서 검증합니다.
            validated_results["country"] = CountryRecord(**data_to_validate)
            print("✅ [Country] 데이터 검증 통과")
        except ValidationError as e:
            logger.error(f"❌ [Country] 검증 실패:\n{e}")

    # 3) IP 데이터 검증
    if raw_ip := raw_data.get("ip"):
        try:
            # 딕셔너리 언패킹으로 raw_ip를 푼 값을 Pydantic 스키마 IpRecord에서 검증합니다.
            validated_results["ip"] = IpRecord(**raw_ip)
            print("✅ [IP] 데이터 검증 통과")
        except ValidationError as e:
            logger.error(f"❌ [IP] 검증 실패:\n{e}")

    print("--- 검증 종료 ---\n")
    return validated_results
