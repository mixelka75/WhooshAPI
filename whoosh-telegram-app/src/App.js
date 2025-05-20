import React, { useState, useEffect, useCallback } from 'react';

// Компонент для адаптации к теме Telegram
const TelegramApp = () => {
  // Состояния приложения
  const [scooterCode, setScooterCode] = useState('');
  const [activeTrip, setActiveTrip] = useState(null);
  const [minutePack, setMinutePack] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  // Базовый URL API - используем относительные пути
  const API_BASE_URL = '';

  // Определяем функцию endTrip с помощью useCallback, чтобы её можно было использовать в эффектах
  const endTrip = useCallback(async (tripId) => {
    if (!tripId) return;

    // Защита от повторных запросов, если уже идет загрузка
    if (loading) {
      console.log('Запрос уже выполняется, игнорируем повторное нажатие');
      return;
    }

    console.log(`Вызвана функция завершения поездки ${tripId}`);
    setLoading(true);
    setError(null);

    try {
      console.log(`Отправка запроса на завершение поездки ${tripId}...`);
      const response = await fetch(`${API_BASE_URL}/api/end_trip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          trip_id: tripId
        })
      });

      // Получаем json-данные даже при ошибке
      let data;
      try {
        data = await response.json();
        console.log('Ответ от сервера при завершении поездки:', data);
      } catch (jsonError) {
        console.error('Ошибка при парсинге JSON ответа:', jsonError);
        data = { success: false, detail: 'Ошибка формата ответа сервера' };
      }

      if (!response.ok) {
        // Получаем сообщение ошибки или используем стандартное
        const errorMessage = data.detail || data.message || `Ошибка сервера: ${response.status}`;
        throw new Error(errorMessage);
      }

      if (data.success) {
        // Если поездка успешно завершена
        console.log('Поездка успешно завершена');

        // Показываем результат поездки
        if (window.Telegram && window.Telegram.WebApp) {
          window.Telegram.WebApp.showPopup({
            title: 'Поездка завершена',
            message: `Длительность: ${data.duration_formatted}\nРасстояние: ${data.distance} км\nСтоимость: ${data.final_cost/100} ₽`,
            buttons: [{ type: 'ok' }]
          });
        }

        // Сбрасываем активную поездку и обновляем информацию о пакете минут
        // ВАЖНО: Делаем это после показа попапа
        setActiveTrip(null);
        fetchMinutePack();

        // Добавляем небольшую задержку перед запросом статуса поездки,
        // чтобы дать серверу время обновить статус
        setTimeout(() => {
          fetchTripInfo();
        }, 1000);
      } else {
        setError(data.detail || data.message || 'Не удалось завершить поездку');
        // Проверяем, действительно ли поездка всё еще активна
        fetchTripInfo(tripId);
      }
    } catch (err) {
      console.error('Ошибка при завершении поездки:', err);
      setError(err.message || 'Ошибка при завершении поездки');

      // Проверяем статус поездки после ошибки
      fetchTripInfo(tripId);
    } finally {
      setLoading(false);
    }
  }, [loading]); // Зависимость только от loading

  // Инициализация и настройка темы
  useEffect(() => {
    console.log('Инициализация приложения...');

    // Проверяем, что Telegram Web App доступен
    if (window.Telegram && window.Telegram.WebApp) {
      console.log('Telegram WebApp API доступен, версия:', window.Telegram.WebApp.version);

      // Сообщаем Telegram, что приложение готово к отображению
      window.Telegram.WebApp.ready();

      // Устанавливаем слушатель на изменение темы
      window.Telegram.WebApp.onEvent('themeChanged', updateTheme);

      // Применяем начальную тему
      updateTheme();
    } else {
      console.warn('Telegram WebApp API не доступен');
    }

    // Выполняем первичную проверку поездки
    fetchTripInfo();
    fetchMinutePack();

    setInitialLoading(false);

    return () => {
      // Удаляем слушатели при размонтировании компонента
      if (window.Telegram && window.Telegram.WebApp) {
        console.log('Удаление обработчиков событий при размонтировании');
        window.Telegram.WebApp.offEvent('themeChanged', updateTheme);
      }
    };
  }, []); // Пустой массив зависимостей для выполнения только при монтировании

  // Обновление MainButton при изменении состояния activeTrip
  useEffect(() => {
    if (!window.Telegram || !window.Telegram.WebApp) return;

    const tg = window.Telegram.WebApp;

    // Очищаем любые предыдущие обработчики клика
    if (tg.MainButton) {
      tg.MainButton.offClick();
    }

    if (activeTrip) {
      console.log('Активная поездка обнаружена, настраиваем MainButton');

      // Настраиваем основную кнопку
      tg.MainButton.setText('Завершить поездку');
      tg.MainButton.show();

      // ВАЖНО: Устанавливаем обработчик напрямую через onClick
      tg.MainButton.onClick(() => {
        console.log('Клик по MainButton!');
        if (activeTrip && activeTrip.trip_id) {
          endTrip(activeTrip.trip_id);
        }
      });
    } else {
      console.log('Активная поездка не обнаружена, скрываем MainButton');
      tg.MainButton.hide();
    }

    // Обязательно очищаем обработчик при размонтировании или изменении зависимостей
    return () => {
      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.MainButton) {
        window.Telegram.WebApp.MainButton.offClick();
      }
    };
  }, [activeTrip, endTrip]); // Включаем endTrip в зависимости!

  // Обновление состояния MainButton при изменении loading
  useEffect(() => {
    if (!window.Telegram || !window.Telegram.WebApp || !window.Telegram.WebApp.MainButton) return;

    const MainButton = window.Telegram.WebApp.MainButton;

    if (loading) {
      console.log('Загрузка - отключаем кнопку и показываем прогресс');
      MainButton.disable();
      MainButton.showProgress(true);
    } else {
      console.log('Загрузка завершена - включаем кнопку и скрываем прогресс');
      MainButton.hideProgress();
      MainButton.enable();
    }
  }, [loading]);

  // ВАЖНО: Проверка статуса поездки каждую секунду
  useEffect(() => {
    // Каждую секунду проверяем статус поездки
    const tripInfoInterval = setInterval(() => {
      fetchTripInfo();
    }, 1000);

    // Очистка при размонтировании
    return () => {
      clearInterval(tripInfoInterval);
    };
  }, []);

  // Получение информации о пакете минут каждые 5 секунд
  useEffect(() => {
    const minutePackInterval = setInterval(() => {
      fetchMinutePack();
    }, 5000);

    return () => {
      clearInterval(minutePackInterval);
    };
  }, []);

  // Функция обновления темы
  const updateTheme = () => {
    if (!window.Telegram || !window.Telegram.WebApp) return;

    const themeParams = window.Telegram.WebApp.themeParams;

    // Применяем CSS переменные темы для использования в стилях
    document.documentElement.style.setProperty('--bg-color', themeParams.bg_color);
    document.documentElement.style.setProperty('--text-color', themeParams.text_color);
    document.documentElement.style.setProperty('--hint-color', themeParams.hint_color);
    document.documentElement.style.setProperty('--link-color', themeParams.link_color);
    document.documentElement.style.setProperty('--button-color', themeParams.button_color);
    document.documentElement.style.setProperty('--button-text-color', themeParams.button_text_color);
    document.documentElement.style.setProperty('--secondary-bg-color', themeParams.secondary_bg_color || '#f0f0f0');
  };

  // Получение информации о поездке - просто проверка наличия активной поездки
  const fetchTripInfo = async (tripId = null) => {
    try {
      console.log('Проверка статуса поездки...');
      const response = await fetch(`${API_BASE_URL}/api/trip_info${tripId ? `?trip_id=${tripId}` : ''}`, {
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        console.error(`Ошибка API при получении статуса поездки: ${response.status}`);
        return; // Просто выходим из функции, не обновляя состояние
      }

      const data = await response.json();
      console.log('Получен статус поездки:', data);

      // Проверяем результат и обновляем состояние активной поездки
      if (data.active_trip) {
        setActiveTrip(data);
      } else {
        // Если активной поездки нет, но сообщение "Нет активных поездок",
        // то это нормальная ситуация, не ошибка
        if (data.message === "Нет активных поездок") {
          // Молча обновляем состояние
          setActiveTrip(null);
          setError(null); // Очищаем ошибку, если она была
        } else if (data.status === "None") {
          // Обрабатываем специфический случай со статусом None
          console.log('Получен статус None, это нормально после завершения поездки');
          setActiveTrip(null);
          setError(null); // Очищаем ошибку, чтобы не показывать "неожиданный статус None"
        }
      }
    } catch (err) {
      console.error('Ошибка при получении информации о поездке:', err);
      // Не сбрасываем активную поездку при ошибке соединения
    }
  };

  // Получение информации о пакете минут
  const fetchMinutePack = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/minute_pack`, {
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка API: ${response.status}`);
      }

      const data = await response.json();
      setMinutePack(data);
    } catch (err) {
      console.error('Ошибка при получении информации о пакете минут:', err);
    }
  };

  // Начало поездки
  const startTrip = async () => {
    if (!scooterCode.trim()) {
      setError('Введите код самоката');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/start_trip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          code: scooterCode.trim()
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Ошибка API: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setActiveTrip(data);
        setScooterCode('');

        // После успешного начала поездки сразу запрашиваем актуальную информацию
        fetchTripInfo(data.trip_id);
      } else {
        setError(data.detail || 'Не удалось начать поездку');
      }
    } catch (err) {
      setError(err.message || 'Ошибка при начале поездки');
      console.error('Ошибка при начале поездки:', err);
    } finally {
      setLoading(false);
    }
  };

  // Отладочная функция для прямого вызова завершения поездки
  const debugEndTrip = () => {
    if (activeTrip && activeTrip.trip_id) {
      console.log('Вызываем завершение поездки напрямую...');
      endTrip(activeTrip.trip_id);
    } else {
      console.log('Нет активной поездки для завершения');
    }
  };

  if (initialLoading) {
    return <div className="loading-screen">Загрузка...</div>;
  }

  return (
    <div className="app-container">
      {/* Информация о пакете минут */}
      {minutePack && (
        <div className="minute-pack-info">
          {minutePack.has_minute_pack ? (
            <div className="minute-pack-available">
              <div className="pack-name">{minutePack.pack_name}</div>
              <div className="pack-time-left">{minutePack.formatted_time_left}</div>
              <div className="pack-duration">{minutePack.duration}</div>
            </div>
          ) : (
            <div className="minute-pack-unavailable">
              У вас нет активного пакета минут
            </div>
          )}
        </div>
      )}

      {/* Основной контент */}
      <div className="main-content">
        {activeTrip ? (
          // Экран активной поездки
          <div className="active-trip-container">
            <h2>Поездка активна</h2>

            <div className="trip-info">
              <div className="info-row">
                <span className="info-label">Самокат:</span>
                <span className="info-value">{activeTrip.device_code}</span>
              </div>

              <div className="info-row">
                <span className="info-label">Время в пути:</span>
                <span className="info-value">{activeTrip.duration_formatted}</span>
              </div>

              <div className="info-row">
                <span className="info-label">Заряд батареи:</span>
                <span className="info-value">{activeTrip.battery_level}%</span>
              </div>

              <div className="info-row">
                <span className="info-label">Режим скорости:</span>
                <span className="info-value">{activeTrip.speed_mode}</span>
              </div>

              {activeTrip.distance > 0 && (
                <div className="info-row">
                  <span className="info-label">Пройдено:</span>
                  <span className="info-value">{activeTrip.distance} км</span>
                </div>
              )}

              {activeTrip.current_cost > 0 && (
                <div className="info-row">
                  <span className="info-label">Текущая стоимость:</span>
                  <span className="info-value">{activeTrip.current_cost/100} ₽</span>
                </div>
              )}
            </div>

            {/* Отладочная кнопка на случай проблем с MainButton */}
            <div style={{display: 'none'}}>
              <button
                onClick={debugEndTrip}
                className="debug-button"
              >
                Завершить поездку (отладка)
              </button>
            </div>

            {/* Отображаем ошибку, только если это не ошибка о статусе None */}
            {error && !error.includes('статус None') && (
              <div className="error-message">{error}</div>
            )}
          </div>
        ) : (
          // Экран ввода кода самоката
          <div className="input-container">
            <h2>Начать поездку</h2>

            <div className="scooter-input-group">
              <input
                type="text"
                className="scooter-code-input"
                placeholder="Введите код самоката"
                value={scooterCode}
                onChange={(e) => setScooterCode(e.target.value)}
                disabled={loading}
              />

              <button
                className="start-trip-button"
                onClick={startTrip}
                disabled={loading || !scooterCode.trim()}
              >
                {loading ? 'Начинаем...' : 'Поехали!'}
              </button>
            </div>

            {/* Отображаем общие ошибки, но игнорируем ошибки о статусе None после завершения поездки */}
            {error && !error.includes('статус None') && (
              <div className="error-message">{error}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Глобальные стили для приложения
const AppStyles = () => (
  <style>{`
    :root {
      --bg-color: #ffffff;
      --text-color: #000000;
      --hint-color: #999999;
      --link-color: #2481cc;
      --button-color: #2481cc;
      --button-text-color: #ffffff;
      --secondary-bg-color: #f0f0f0;
    }
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      padding: 16px;
    }
    
    .loading-screen {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      font-size: 18px;
      color: var(--hint-color);
    }
    
    .app-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
      max-width: 500px;
      margin: 0 auto;
    }
    
    .minute-pack-info {
      background-color: var(--secondary-bg-color);
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 8px;
    }
    
    .minute-pack-available {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    
    .pack-name {
      font-weight: bold;
    }
    
    .pack-time-left {
      font-size: 18px;
      font-weight: bold;
      color: var(--button-color);
    }
    
    .pack-duration {
      font-size: 12px;
      color: var(--hint-color);
    }
    
    .minute-pack-unavailable {
      color: var(--hint-color);
    }
    
    .main-content {
      background-color: var(--bg-color);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    h2 {
      margin-bottom: 16px;
      font-size: 18px;
      text-align: center;
    }
    
    .input-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .scooter-input-group {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .scooter-code-input {
      padding: 12px;
      border: 1px solid var(--hint-color);
      border-radius: 8px;
      font-size: 16px;
      background-color: var(--bg-color);
      color: var(--text-color);
    }
    
    .scooter-code-input:focus {
      outline: none;
      border-color: var(--button-color);
    }
    
    .scooter-code-input::placeholder {
      color: var(--hint-color);
    }
    
    .start-trip-button, .debug-button {
      padding: 12px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: bold;
      background-color: var(--button-color);
      color: var(--button-text-color);
      cursor: pointer;
      transition: opacity 0.2s;
    }
    
    .start-trip-button:disabled, .debug-button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .error-message {
      color: #ff3b30;
      font-size: 14px;
      text-align: center;
      margin-top: 8px;
    }
    
    .active-trip-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .trip-info {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 16px;
    }
    
    .info-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid var(--secondary-bg-color);
    }
    
    .info-label {
      color: var(--hint-color);
    }
    
    .info-value {
      font-weight: bold;
    }
    
    .debug-button {
      margin-top: 8px;
      background-color: #ffa500;
    }
  `}</style>
);

// Главный компонент приложения
const App = () => {
  return (
    <>
      <AppStyles />
      <TelegramApp />
    </>
  );
};

export default App;