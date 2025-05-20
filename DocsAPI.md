# WhooshAPI - Подробная документация API

## Содержание
1. [Введение](#введение)
2. [Аутентификация](#аутентификация)
3. [Базовые эндпоинты](#базовые-эндпоинты)
4. [Эндпоинты для управления поездками](#эндпоинты-для-управления-поездками)
5. [Эндпоинты для бронирования](#эндпоинты-для-бронирования)
6. [Эндпоинты для работы с аккаунтом](#эндпоинты-для-работы-с-аккаунтом)
7. [Коды ответов и обработка ошибок](#коды-ответов-и-обработка-ошибок)
8. [Примеры использования](#примеры-использования)

## Введение

WhooshAPI представляет собой обертку вокруг официального API сервиса аренды электросамокатов Whoosh. API построено с использованием FastAPI и предоставляет удобный интерфейс для взаимодействия с сервисом Whoosh из ваших приложений.

Базовый URL API: `http://your-server:8031`

## Аутентификация

API использует систему токенов Whoosh для аутентификации запросов. Токены хранятся в файле `whoosh_tokens.json` и автоматически обновляются при необходимости.

Для начальной настройки необходимо получить `refresh_token` из официального приложения Whoosh и добавить его в файл `whoosh_tokens.json`:

```json
{
  "access_token": "",
  "id_token": "",
  "refresh_token": "ваш_рефреш_токен_здесь"
}
```

При запуске сервера токены будут автоматически обновлены и использованы для всех запросов. Токены имеют ограниченный срок действия (обычно 1 час), после чего автоматически обновляются при следующем запросе.

### Ручное обновление токенов

```http
POST /api/refresh_tokens
```

**Ответ:**
```json
{
  "success": true,
  "message": "Токены успешно обновлены",
  "expires_in": "1 час"
}
```

## Базовые эндпоинты

### Получение информации о пакете минут

```http
GET /api/minute_pack
```

**Успешный ответ (если есть пакет минут):**
```json
{
  "has_minute_pack": true,
  "pack_name": "Название пакета",
  "minutes_left": 120,
  "seconds_left": 7200,
  "formatted_time_left": "120 мин 0 сек",
  "valid_to": "2025-06-20T15:30:00Z",
  "duration": "24 часа"
}
```

**Успешный ответ (если нет пакета минут):**
```json
{
  "has_minute_pack": false
}
```

## Эндпоинты для управления поездками

### Начало поездки

```http
POST /api/start_trip
Content-Type: application/json

{
  "code": "ABCDEF"  // Код самоката
}
```

**Успешный ответ:**
```json
{
  "success": true,
  "trip_id": "идентификатор_поездки",
  "device_code": "ABCDEF",
  "device_id": "идентификатор_устройства",
  "using_minute_pack": true,
  "message": "Поездка успешно начата",
  "status": "ACTIVE",
  "battery_level": 75
}
```

### Получение информации о поездке

```http
GET /api/trip_info
```

или

```http
GET /api/trip_info?trip_id=идентификатор_поездки
```

**Успешный ответ (если есть активная поездка):**
```json
{
  "active_trip": true,
  "trip_id": "идентификатор_поездки",
  "duration": 300,
  "duration_formatted": "300 с",
  "device_code": "ABCDEF",
  "battery_level": 74,
  "current_cost": 5000,
  "distance": 0.3,
  "speed_mode": "NORMAL",
  "coordinates": {
    "lat": 55.767123,
    "lng": 37.586001
  }
}
```

**Успешный ответ (если нет активной поездки):**
```json
{
  "active_trip": false,
  "message": "Нет активных поездок"
}
```

### Завершение поездки

```http
POST /api/end_trip
Content-Type: application/json

{
  "trip_id": "идентификатор_поездки"
}
```

**Успешный ответ:**
```json
{
  "success": true,
  "trip_id": "идентификатор_поездки",
  "status": "COMPLETED",
  "duration": 480,
  "duration_formatted": "480 с",
  "distance": 0.5,
  "final_cost": 8000,
  "minute_pack": {
    "active": true,
    "minutes_left": 119
  },
  "message": "Поездка успешно завершена"
}
```

## Эндпоинты для бронирования

### Бронирование самоката

```http
POST /api/reserve_scooter/{scooter_code}
```

**Успешный ответ:**
```json
{
  "success": true,
  "reservation_id": "идентификатор_бронирования",
  "scooter_code": "ABCDEF",
  "device_id": "идентификатор_устройства",
  "created_at": "2025-05-20T12:00:00Z",
  "expires_at": "2025-05-20T12:20:00Z",
  "battery_level": 75,
  "scooter_model": "Model X",
  "coordinates": {
    "lat": 55.767123,
    "lng": 37.586001
  },
  "message": "Самокат успешно забронирован до 2025-05-20T12:20:00Z"
}
```

### Отмена бронирования

```http
DELETE /api/cancel_reservation/{reservation_id}
```

**Успешный ответ:**
```json
{
  "success": true,
  "reservation_id": "идентификатор_бронирования",
  "created_at": "2025-05-20T12:00:00Z",
  "started_at": "2025-05-20T12:00:00Z",
  "finished_at": "2025-05-20T12:05:00Z",
  "status": "CANCELLED",
  "message": "Бронирование успешно отменено"
}
```

### Начало поездки по бронированию

```http
POST /api/start_reserved_trip
Content-Type: application/json

{
  "deviceCode": "ABCDEF"  // Код самоката
}
```

**Успешный ответ:**
```json
{
  "success": true,
  "trip_id": "идентификатор_поездки",
  "scooter_code": "ABCDEF",
  "created_at": "2025-05-20T12:00:00Z",
  "status": "ACTIVE",
  "battery_level": 75,
  "reservation": {
    "id": "идентификатор_бронирования",
    "created_at": "2025-05-20T11:50:00Z",
    "status": "COMPLETED"
  },
  "message": "Поездка по бронированию успешно начата"
}
```

### Получение информации о текущих бронированиях

```http
GET /api/active_reservations
```

**Успешный ответ:**
```json
{
  "active_reservations": [
    {
      "reservation_id": "идентификатор_бронирования",
      "scooter_code": "ABCDEF",
      "created_at": "2025-05-20T12:00:00Z",
      "expires_at": "2025-05-20T12:20:00Z",
      "status": "ACTIVE",
      "device_id": "идентификатор_устройства",
      "battery_level": 75
    }
  ],
  "count": 1
}
```

## Эндпоинты для работы с аккаунтом

### Получение информации об аккаунте

```http
GET /api/account
```

**Успешный ответ:**
```json
{
  "id": "идентификатор_пользователя",
  "name": "Иван Иванов",
  "phone": "+79001234567",
  "email": "example@email.com",
  "locale": "ru",
  "trips_count": 42,
  "birthdate": "1990-01-01",
  "verified": true,
  "verified_birthdate": true,
  "gender": "MALE",
  "verified_gender": true,
  "auth_types": ["PHONE"],
  "debtor": false
}
```

### Получение платежных методов

```http
GET /api/payment_methods
```

**Успешный ответ:**
```json
{
  "payment_methods": [
    {
      "id": "идентификатор_метода_оплаты",
      "type": "CARD",
      "card_type": "VISA",
      "number": "************1234",
      "rbs_type": "VISA",
      "status": "ACTIVE",
      "preferable": true,
      "last_successful_charge": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1,
  "has_preferred_method": true
}
```

### Получение подписок пользователя

```http
GET /api/subscriptions
```

**Успешный ответ:**
```json
{
  "active_subscriptions": [
    {
      "id": "идентификатор_подписки",
      "title": "Премиум",
      "name": "premium",
      "status": "ACTIVE",
      "valid_from": "2025-04-20T12:00:00Z",
      "valid_to": "2025-05-20T12:00:00Z",
      "price": 699,
      "currency": "RUB",
      "auto_prolongation": true,
      "is_trial": false
    }
  ],
  "expired_subscriptions": [],
  "on_hold_subscriptions": [],
  "has_active_subscription": true,
  "active_until": "2025-05-20T12:00:00Z"
}
```

### Получение доступных предложений подписок

```http
GET /api/subscription_offers
```

**Успешный ответ:**
```json
{
  "subscription_offers": [
    {
      "id": "идентификатор_предложения",
      "title": "Премиум на месяц",
      "name": "premium_monthly",
      "is_trial": false,
      "price": 699,
      "currency": "RUB",
      "version": 1,
      "features": [
        "Приоритетная поддержка",
        "Специальные тарифы",
        "Бесплатная разблокировка"
      ],
      "illustration_url": "https://example.com/premium_illustration.png"
    }
  ],
  "count": 1
}
```

## Коды ответов и обработка ошибок

API использует стандартные HTTP коды состояния:

- **200 OK** - запрос выполнен успешно
- **400 Bad Request** - ошибка в параметрах запроса
- **401 Unauthorized** - ошибка авторизации
- **404 Not Found** - запрошенный ресурс не найден
- **500 Internal Server Error** - внутренняя ошибка сервера

В случае ошибки API возвращает JSON-объект с информацией об ошибке:

```json
{
  "detail": "Описание ошибки"
}
```

или

```json
{
  "success": false,
  "detail": "Описание ошибки",
  "message": "Сообщение об ошибке"
}
```

## Примеры использования

### Пример: Начало поездки и ее завершение

1. Проверка наличия пакета минут:

```http
GET /api/minute_pack
```

2. Начало поездки:

```http
POST /api/start_trip
Content-Type: application/json

{
  "code": "KE446A"
}
```

3. Получение информации о поездке:

```http
GET /api/trip_info
```

4. Завершение поездки:

```http
POST /api/end_trip
Content-Type: application/json

{
  "trip_id": "полученный_идентификатор_поездки"
}
```

### Пример: Бронирование самоката

1. Бронирование самоката:

```http
POST /api/reserve_scooter/KE446A
```

2. Проверка статуса бронирования:

```http
GET /api/active_reservations
```

3. Начало поездки по бронированию:

```http
POST /api/start_reserved_trip
Content-Type: application/json

{
  "deviceCode": "KE446A"
}
```

### Специфика взаимодействия с API

1. Все запросы к API автоматически используют токены авторизации, которые обновляются при необходимости
2. Координаты начала и завершения поездки фиксированы в коде сервера (см. константы DEFAULT_LAT, DEFAULT_LNG и END_COORDINATES в main.py)
3. Для продакшн-использования рекомендуется ограничить CORS через настройку allow_origins в main.py

## Telegram Mini App интеграция

React-приложение в директории `whoosh-telegram-app` предназначено для использования внутри Telegram. Оно взаимодействует с API и использует Telegram Web App API для интеграции с интерфейсом Telegram.

Ключевые особенности интеграции:
- Адаптация к светлой и темной теме Telegram
- Использование MainButton Telegram для завершения поездки
- Показ уведомлений через стандартные диалоги Telegram
- Автоматическое обновление информации о поездке

Для интеграции в Telegram бота:
1. Создайте бота через @BotFather
2. Настройте Web App URL для бота, указав адрес вашего API сервера
3. Добавьте кнопку в меню бота для запуска Web App