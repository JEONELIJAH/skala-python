"""
파일명: collector.py
작성자: 전우진 P267
작성일: 2026-08-06
설명: httpx와 asyncio를 활용하여 외부 API 데이터를 
      비동기 방식으로 동시에 수집하는 모듈입니다.
"""

import asyncio
import logging

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 데이터 수집을 위한 사용 API 정의
WEATHER_URL = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&hourly=temperature_2m,precipitation_probability&forecast_days=3&timezone=Asia/Seoul"
COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"

# API를 비동기로 호출하는 함수입니다.
async def fetch_api(client, url, name):
    try:
        # await로 응답이 올 때까지 스레드를 블락하지 않고 다른 작업을 합니다.
        response = await client.get(url, timeout=10)
        
        # HTTP 상태 코드가 4xx, 5xx일 경우 예외를 발생시킵니다.
        response.raise_for_status()
        
        logger.info(f"✅ [{name}] API 수집 완료")
        return {"name": name, "data": response.json()}

    # raise_for_status로부터 받은 에러 처리
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ [{name}] HTTP 에러 발생: {e.response.status_code}")
        return {"name": name, "error": str(e)}
    except httpx.RequestError as e:
        logger.error(f"❌ [{name}] API 연결 실패: {e}")
        return {"name": name, "error": str(e)}

# 3개의 API를 동시에 수집하는 메인 파이프라인 함수입니다.
async def collect_all_data():
    
    # async with를 사용하여 통신이 종료될 때 client를 자동으로 닫습니다.
    # 클라이언트는 httpx.AsyncClient로 정의하여 비동기 HTTP 클라이언트를 사용했습니다.
    async with httpx.AsyncClient() as client:
        print("\n--- 📡 비동기 API 데이터 수집 시작 ---\n")
        
        # 작업 리스트
        tasks = [
            fetch_api(client, WEATHER_URL, "weather"),
            fetch_api(client, COUNTRY_URL, "country"),
            fetch_api(client, IP_URL, "ip")
        ]
        
        # asyncio.gather를 사용해서 리스트에 담긴 여러 태스크들을 동시에 실행하고, 전부 끝날 때까지 기다립니다.
        # return_exceptions=True로 일부 실패를 허용했습니다.
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n--- 수집 종료 ---\n")
        
        # 수집된 결과를 컴프리헨션을 사용해 딕셔너리로 묶어서 반환합니다.
        collected_data = {res["name"]: res.get("data") for res in results}
        return collected_data

# if __name__ == "__main__":
#     from schemas import validate_data

#     # asyncio.run()로 이벤트 루프를 시작합니다.
#     raw_data = asyncio.run(collect_all_data())

#     # 수집한 데이터를 정의한 Pydantic schemas에서 검증합니다.
#     validated_data = validate_data(raw_data)
    
#     # 객체로 변환된 결과물을 확인합니다.
#     print("\n[데이터 확인]")
#     if weather_list := validated_data.get("weather"):
#         # Pydantic 객체에 model_dump()를 사용해서 딕셔너리로 불 수 있게 했습니다.
#         print(f"날씨 정보: {weather_list[0].model_dump()}")

#     if validated_data.get("ip"):
#         print(f"IP 정보: {validated_data['ip'].model_dump()}")
        
#     if validated_data.get("country"):
#         print(f"국가 정보: {validated_data['country'].model_dump()}")
