from fastapi import FastAPI, HTTPException, Query,  Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import httpx
import uvicorn
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import logging
import uuid
from datetime import datetime

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whoosh API Wrapper", description="Упрощенный API для сервиса аренды самокатов Whoosh")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшн-окружении лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whoosh-telegram-app/build")

# Монтируем статические файлы React приложения
app.mount("/static", StaticFiles(directory=os.path.join(STATIC_DIR, "static")), name="static")

# Пути к файлам с конфигурацией и токенами
TOKENS_FILE = "whoosh_tokens.json"
CONFIG_FILE = "whoosh_config.json"

# Настройки по умолчанию
BASE_URL = "https://api.whoosh.bike"
COGNITO_URL = "https://cognito.whoosh.bike/"
REGION_ID = "773ff572-49a8-4619-b291-290f1f3e4271"
CLIENT_UUID = "c027fc25-d406-33c4-867a-dc2e3d071b60"
CLIENT_ID = "7g1h82vpnjve0omfq1ssko18gl"

# Координаты пользователя (неизменные, как указано в требованиях)
DEFAULT_LAT = 55.766845
DEFAULT_LNG = 37.585954

# Координаты для завершения поездки (неизменные, как указано в требованиях)
END_COORDINATES = {
    "lat": 55.767656,
    "lng": 37.587952
}


# Функция для загрузки токенов из файла
def load_tokens():
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при загрузке токенов: {str(e)}")

    # Возвращаем пустую структуру, если файл не существует или произошла ошибка
    return {
        "access_token": None,
        "id_token": None,
        "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.ZayegTCQ0WNjKwIbXRHb0KRkn3vLBUy3fbZob8x7_5fheeEdruI-utbDWvFYQAcZS0ZA6mFIjF24IkNb92noOPYmZTNGXxfqPMcuAIHM_ZfZzG_GzipALvTvCG0UOo-4YOGJfMKxtr94JToTE7tlKSyjk3VCGEchNWpiiO5wewdMz45EdSR5YLp-k7owqdmVA9dhZ1k3WC1LrV4MhKdsAlckF-fYTGLkwQZlByEp_2wabKVMHO6pQdZ17voehd3vRw0MX6DNR-nqOiZeYK_QTiHKs0RFUfDuthgh6iGHgk5gSEmjuuBvBsi8IJMvqdFVBFPNss2jcUWSXfZN_8tCgg.Uod42xmrKHbXHlOG.janCXpIgrMfSEG95BwbzbVb8ljjeBIzeg41OQR9RYNOxRMVC_n40ajIiWvkTE2L3_1F0MYbr75wmTIObpH-Dy46ZW-arsKDHqrtNyDovvU2LCio8ubQY_Y_02BMcmKZS_z-ce-XNXkdvIlI2-lOYoKX4K3cx6yRLUZv7ugvrR8VBYulwmdqd90RUugAM_0Ra__B-K9QeMDFTAncUaGvVNE_CzesdFUBckXpRb1Q-oE3EFVRcde0-sTkjc4H_c5q6LKnHMORtb-NA1KDNnEj8Og1bNbSPbFuNW5oletmfM2t8mvtdlYTnvW70f0y1IukduUVOKkxnAct8_S3q_cX0h9CDYpkiX5A2wVboysOP_hNEIqxrlkrMW-t0EbAn6BQHYC9EDAEV_Klyn6_3HKWE-WYbOUw0P4WxwKZLW3sv9wOWhh_WgFAs_itTIZ_s-iiR-0DOxelLdW7odp_c8cUCTpnVBhJVu_UcekfaEOjSfnOsiRprgqobH4UDeNsq4kJIh7si43Pob7q6THMlAngC3kSTJPdqQFSik4aLT2UKpwRa-pPe9tCBwlwcsHHeMIidD7bFBmcaqj5rcOBBpPujciAZflStWOhjk9PD6jzfGbIE5aYfbfsLxlBE8Re_rYIdVKiJIIIhjvtvGzn2J_G1DIKj4lw4DHaewmC0XpQICvbR5tjPhUc-EKqQVKOMQIBBToE_VYg42L6RPP0pyjhS5QJ6un8x_Wzz6B7Gpk_3uFFVvF9R-_diyGtBjZ75gyiah50eM-P0BzvvFCJ5lrdruqkiDBMITqWC4VELQDjig8T3pqdufeyT3yUFVBeoAK3OICqC33QPhKsd1OjlIX2FyaEvkk4gmOo8Z0L2AKZLftotwWayybuKlQtZNEYhGKLqT1X-OCAR8nog9k0Log_mxyuxpje8VYQxxDNaOF68T-CW9rQHlwQ3BCo1iuf23ShUh7osFpL1KNDQzD9NSOqf2snnwTM43UNvZbQg1jaWe6ImR8ZGAWaCcpI43oCH5FR0lbLLo1QScGW-Xqf8ceMTZqYZ781inhIQMFPPpFhxbjSN7ZmmzFmEq078FBQ6tA_19LejdC8I8ENi3e7iBfzk2s0O8pSSRSrqaKdlRPf_V39RmLBovcYZqtIZuaais_s-r7U8m-rEZqKF0j_-oOPEamXwwCknUaGY5YFZC2EicBOPxgfoCI2yIzk2IyAMgkSWLo0Ib_B6HZxhcmmSpdx22c0ufGadAoLfSUMTKyrlsKcKenz6dKX4L_YhYNu5bR0Ki8Lj_Z55j2QOyo0kFXKbbvy3jvbVcwIfxmvds0HOCE_0i0hX-SZwLhecf-ts8g.SHGIIgfcM22Z-HPrq33fiA"
    }


# Функция для сохранения токенов в файл
def save_tokens(tokens):
    try:
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении токенов: {str(e)}")


# Функция для обновления токенов
async def refresh_tokens():
    tokens = load_tokens()

    if not tokens.get("refresh_token"):
        raise HTTPException(status_code=401, detail="Отсутствует refresh_token. Требуется полная авторизация.")

    # Формируем запрос на обновление токенов
    headers = {
        "Accept-Encoding": "identity",
        "aws-sdk-invocation-id": str(uuid.uuid4()),
        "aws-sdk-retry": "0/0",
        "Content-Type": "application/x-amz-json-1.1",
        "Host": "cognito.whoosh.bike",
        "User-Agent": "aws-sdk-android/2.22.5 Linux/4.19.278-g7b0944645172-ab10812814 Dalvik/2.1.0/0 ru_RU",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"
    }

    data = {
        "AuthFlow": "REFRESH_TOKEN_AUTH",
        "AuthParameters": {
            "REFRESH_TOKEN": tokens["refresh_token"]
        },
        "ClientId": CLIENT_ID,
        "UserContextData": {}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(COGNITO_URL, headers=headers, json=data)

            if response.status_code != 200:
                logger.error(f"Ошибка при обновлении токенов: {response.text}")
                raise HTTPException(status_code=response.status_code,
                                    detail=f"Ошибка при обновлении токенов: {response.text}")

            refresh_data = response.json()
            auth_result = refresh_data.get("AuthenticationResult", {})

            # Обновляем токены
            tokens["access_token"] = auth_result.get("AccessToken")
            tokens["id_token"] = auth_result.get("IdToken")
            # refresh_token не меняется при обновлении

            # Сохраняем обновленные токены
            save_tokens(tokens)

            return tokens
    except httpx.HTTPError as e:
        logger.error(f"Ошибка HTTP при обновлении токенов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении токенов: {str(e)}")


# Модели данных
class ScooterCode(BaseModel):
    code: str  # Код самоката (например KE446A)


class EndTripRequest(BaseModel):
    trip_id: str


# Вспомогательная функция для запросов к API Whoosh с автоматическим обновлением токенов
async def make_request(
        method: str,
        url: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
) -> Dict:
    if retry_count > 1:
        raise HTTPException(status_code=500, detail="Превышено количество попыток запроса")

    tokens = load_tokens()

    # Если токены отсутствуют, пытаемся обновить их
    if not tokens.get("access_token") or not tokens.get("id_token"):
        tokens = await refresh_tokens()

    headers = {
        "X-Api-Key": "yqKeRnxGX77NSeqvX3YyQ5VBio3SJcJ44iOfOnBX",
        "X-Api-Version": "1.0",
        "X-Auth-Token": tokens["access_token"],
        "X-Id-Token": tokens["id_token"],
        "X-Client": "android",
        "x-client-AB": "A",
        "x-client-uuid": CLIENT_UUID,
        "X-Client-Version": "2.33.0",
        "X-region-id": REGION_ID,
        "Content-Type": "application/json; charset=UTF-8"
    }

    try:
        async with httpx.AsyncClient() as client:
            if method.lower() == "get":
                response = await client.get(url, headers=headers, params=params)
            elif method.lower() == "post":
                response = await client.post(url, headers=headers, json=json_data, params=params)
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")

            # Если токен истек, обновляем токены и повторяем запрос
            if response.status_code == 401 and "expired" in response.text.lower():
                logger.info("Токен истек, обновляем токены...")

                await refresh_tokens()
                # Рекурсивно повторяем запрос с обновленными токенами
                return await make_request(method, url, json_data, params, retry_count + 1)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Ошибка API Whoosh: {response.text}")

            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Ошибка HTTP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении запроса: {str(e)}")


# Эндпоинт для проверки пакета минут
@app.get("/api/minute_pack", summary="Получение информации о пакете минут")
async def get_minute_pack():
    """
    Возвращает информацию о текущем пакете минут пользователя:
    - Наличие активного пакета
    - Количество оставшихся минут/секунд
    - Срок действия пакета
    """
    url = f"{BASE_URL}/user-minute-pack/info"
    params = {"regionId": REGION_ID}

    try:
        response = await make_request("get", url, params=params)

        # Проверяем наличие пакета минут
        if "purchasedMinutePack" in response:
            minute_pack = response["purchasedMinutePack"]
            seconds_left = minute_pack.get("secondsLeft", 0)
            minutes_left = seconds_left // 60
            seconds_remainder = seconds_left % 60

            return {
                "has_minute_pack": True,
                "pack_name": minute_pack.get("annotations", {}).get("packName", ""),
                "minutes_left": minutes_left,
                "seconds_left": seconds_left,
                "formatted_time_left": f"{minutes_left} мин {seconds_remainder} сек",
                "valid_to": minute_pack.get("validTo", ""),
                "duration": minute_pack.get("annotations", {}).get("packDuration", "")
            }
        else:
            return {"has_minute_pack": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации о пакете минут: {str(e)}")


# Эндпоинт для старта поездки
@app.post("/api/start_trip", summary="Начать поездку на самокате")
async def start_trip(scooter: ScooterCode):
    """
    Начинает поездку на выбранном самокате по его коду.
    Координаты пользователя уже предустановлены в системе.
    Автоматически использует пакет минут, если он есть.
    """
    try:
        # Шаг 1: Получаем информацию о самокате по коду
        device_state_url = f"{BASE_URL}/devices/state"
        device_params = {
            "code": scooter.code,
            "lat": DEFAULT_LAT,
            "lng": DEFAULT_LNG,
            "scanType": "MANUAL"
        }

        device_info = await make_request("get", device_state_url, params=device_params)

        device_id = device_info.get("device", {}).get("id")
        if not device_id:
            raise HTTPException(status_code=404, detail="Самокат не найден")

        # Шаг 2: Получаем тарифы для самоката
        tariff_url = f"{BASE_URL}/tariffs/tariff/minute-pack"
        tariff_params = {"device": device_id}

        tariffs_info = await make_request("get", tariff_url, params=tariff_params)

        # Шаг 3: Формируем запрос на начало поездки
        trips_url = f"{BASE_URL}/trips"

        # Копируем тарифы из ответа
        tariffs = tariffs_info.get("tariffs", [])

        trips_data = {
            "deviceCode": scooter.code,
            "startTripType": "MANUAL",
            "insuranceRequired": False,
            "position": {
                "lat": DEFAULT_LAT,
                "lng": DEFAULT_LNG
            },
            "tariffs": tariffs,
            "tariffsToken": tariffs_info.get("tariffsToken", ""),
            "debugData": {
                "sourceType": "trip_device_bs_center_button",
                "uuid": str(uuid.uuid4()),
                "processId": 9119
            }
        }

        # Шаг 4: Отправляем запрос на начало поездки
        trip_response = await make_request("post", trips_url, json_data=trips_data)

        if "trip" not in trip_response:
            raise HTTPException(status_code=500, detail="Не удалось начать поездку: " + str(trip_response))

        trip = trip_response.get("trip", {})
        trip_id = trip.get("id")

        # Проверяем, использовался ли пакет минут
        has_minute_pack = "usersMinutePack" in tariffs_info

        return {
            "success": True,
            "trip_id": trip_id,
            "device_code": scooter.code,
            "device_id": device_id,
            "using_minute_pack": has_minute_pack,
            "message": "Поездка успешно начата",
            "status": trip.get("status"),
            "battery_level": trip.get("device", {}).get("battery", {}).get("power", 0)
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при начале поездки: {str(e)}")


# Эндпоинт для получения информации о текущей поездке
@app.get("/api/trip_info", summary="Получить информацию о текущей поездке")
async def get_trip_info(trip_id: Optional[str] = Query(None, description="ID поездки (если известен)")):
    """
    Возвращает информацию о текущей поездке, включая:
    - Время поездки
    - Пройденное расстояние
    - Текущую стоимость
    - Информацию о самокате
    """
    try:
        # Если ID поездки не указан, получаем активные поездки
        if not trip_id:
            active_trips_url = f"{BASE_URL}/users/logged/active-trips"
            active_trips = await make_request("get", active_trips_url)

            trips = active_trips.get("trips", [])
            if not trips:
                return {"active_trip": False, "message": "Нет активных поездок"}

            # Берем первую активную поездку
            trip_id = trips[0].get("id")

        # Получаем детальную информацию о поездке
        trip_url = f"{BASE_URL}/trips/active/{trip_id}"
        trip_info = await make_request("get", trip_url)

        # Получаем информацию о маршруте
        route_url = f"{BASE_URL}/trips/{trip_id}/route"
        route_info = await make_request("get", route_url)

        # Форматируем и возвращаем данные в удобном виде
        trip = trip_info.get("trip", {})

        return {
            "active_trip": True,
            "trip_id": trip_id,
            "duration": trip.get("duration", {}).get("amount", 0),
            "duration_formatted": f"{trip.get('duration', {}).get('amount', 0)} {trip.get('duration', {}).get('unit', 'с')}",
            "device_code": trip.get("device", {}).get("code", ""),
            "battery_level": trip.get("device", {}).get("battery", {}).get("power", 0),
            "current_cost": trip.get("actualTripCost", {}).get("netPrice", {}).get("amount", 0),
            "distance": trip.get("distance", {}).get("amount", 0),
            "speed_mode": trip.get("device", {}).get("state", {}).get("speedMode", {}).get("current", "NORMAL"),
            "coordinates": trip.get("device", {}).get("state", {}).get("position", {}).get("point", {})
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации о поездке: {str(e)}")


# Исправленный эндпоинт для завершения поездки
@app.post("/api/end_trip", summary="Завершить поездку")
async def end_trip(request: EndTripRequest):
    """
    Завершает текущую поездку с фиксированными координатами
    и возвращает итоговую информацию о поездке.
    """
    try:
        # Сначала проверяем, не завершена ли уже поездка
        try:
            trip_url = f"{BASE_URL}/trips/active/{request.trip_id}"
            trip_info = await make_request("get", trip_url)

            # Если поездка не активна или не найдена, значит она уже завершена
            if "error" in trip_info or trip_info.get("trip", {}).get("status") != "ACTIVE":
                logger.info(f"Поездка {request.trip_id} уже не активна")

                # Возвращаем успешный результат, так как поездка уже завершена
                return {
                    "success": True,
                    "trip_id": request.trip_id,
                    "status": "COMPLETED",
                    "message": "Поездка уже завершена",
                    "duration": 0,
                    "duration_formatted": "0 с",
                    "distance": 0,
                    "final_cost": 0,
                    "minute_pack": {"active": False, "minutes_left": 0}
                }
        except Exception as check_error:
            # Если возникла ошибка при проверке, продолжаем с попыткой завершения
            logger.warning(f"Ошибка при проверке статуса поездки: {str(check_error)}")

        # Данные для завершения поездки
        completion_data = {
            "completeOutsideParking": False,
            "coordinate": END_COORDINATES,
            "payWithScore": False
        }

        logger.info(f"Отправка запроса на завершение поездки {request.trip_id}")

        # Запрос на завершение поездки
        completion_url = f"{BASE_URL}/trips/{request.trip_id}/completion"
        completion_response = await make_request("post", completion_url, json_data=completion_data)

        logger.info(f"Получен ответ от API Whoosh: {completion_response}")

        trip = completion_response.get("trip", {})

        # Проверяем статус поездки в ответе
        trip_status = trip.get("status")
        if trip_status != "COMPLETED":
            logger.error(f"Неожиданный статус поездки: {trip_status}")
            # Не выбрасываем исключение, а возвращаем статус с информацией об ошибке
            return {
                "success": False,
                "message": f"Не удалось завершить поездку: неожиданный статус {trip_status}",
                "trip_id": request.trip_id,
                "status": trip_status
            }

        # Получаем информацию о пакете минут после поездки
        try:
            minute_pack_url = f"{BASE_URL}/user-minute-pack/info"
            minute_pack_params = {"regionId": REGION_ID}

            minute_pack_info = await make_request("get", minute_pack_url, params=minute_pack_params)

            has_minute_pack = "purchasedMinutePack" in minute_pack_info
            minutes_left = 0

            if has_minute_pack:
                seconds_left = minute_pack_info["purchasedMinutePack"].get("secondsLeft", 0)
                minutes_left = seconds_left // 60
        except Exception as minute_pack_error:
            logger.error(f"Ошибка при получении информации о пакете минут: {str(minute_pack_error)}")
            has_minute_pack = False
            minutes_left = 0

        # Успешный ответ
        return {
            "success": True,
            "trip_id": request.trip_id,
            "status": "COMPLETED",
            "duration": trip.get("duration", {}).get("amount", 0),
            "duration_formatted": f"{trip.get('duration', {}).get('amount', 0)} {trip.get('duration', {}).get('unit', 'с')}",
            "distance": trip.get("distance", {}).get("amount", 0),
            "final_cost": trip.get("accruedPricing", {}).get("price", {}).get("amount", 0),
            "minute_pack": {
                "active": has_minute_pack,
                "minutes_left": minutes_left
            },
            "message": "Поездка успешно завершена"
        }

    except HTTPException as e:
        # Записываем конкретную ошибку в лог
        logger.error(f"HTTP ошибка при завершении поездки {request.trip_id}: {str(e)}")

        # Проверяем, возможно поездка уже завершена
        if e.status_code == 404:
            return {
                "success": True,
                "trip_id": request.trip_id,
                "status": "COMPLETED",
                "message": "Поездка успешно завершена (не найдена активная поездка)",
                "duration": 0,
                "duration_formatted": "0 с",
                "distance": 0,
                "final_cost": 0,
                "minute_pack": {"active": False, "minutes_left": 0}
            }

        # Преобразуем HTTPException в понятный JSON ответ
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "detail": str(e.detail),
                "message": "Ошибка при завершении поездки"
            }
        )
    except Exception as e:
        # Записываем общую ошибку в лог
        logger.exception(f"Общая ошибка при завершении поездки {request.trip_id}: {str(e)}")

        # Возвращаем ошибку в удобном формате
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": str(e),
                "message": "Ошибка при завершении поездки"
            }
        )


# Эндпоинт для обновления токенов вручную
@app.post("/api/refresh_tokens", summary="Обновить токены авторизации вручную")
async def manual_refresh_tokens():
    """
    Ручное обновление токенов авторизации.
    Используйте этот эндпоинт, если у вас возникают проблемы с авторизацией.
    """
    try:
        tokens = await refresh_tokens()
        return {
            "success": True,
            "message": "Токены успешно обновлены",
            "expires_in": "1 час"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении токенов: {str(e)}")


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str, request: Request):
    # Если запрос начинается с /api/, возвращаем 404, так как это API маршрут, который не был найден
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Для всех других путей возвращаем индексный HTML файл React приложения
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        raise HTTPException(status_code=404, detail="React build not found")

# Проверяем при запуске, есть ли токены, и если нет - создаем файл
@app.on_event("startup")
async def startup_event():
    tokens = load_tokens()
    if not tokens.get("access_token") or not tokens.get("id_token"):
        logger.info("Токены отсутствуют, попытка получить новые...")
        try:
            await refresh_tokens()
            logger.info("Токены успешно обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении токенов при запуске: {str(e)}")
            # Не прерываем запуск, сервер все равно должен запуститься


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8031, reload=True)