import asyncio, httpx, logging

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
    except Exception as e:
        logger.error(f"❌ [{name}] API 연결 실패: {e}")
        return {"name": name, "error": str(e)}