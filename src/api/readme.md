# Архитектура API SurisleBack
> Актуально на 11 июля 2025 г.

## Базовый URL
https://<your-domain>/api
## Аутентификация

| Шаг | Запрос | Описание |
| --- | ------ | -------- |
| 1. Логин | **POST /auth/login** (src/api/beeline.py) | JSON `{"login":"user","password":"pass"}` → возвращает **accessToken** |
| 2. Токен | Любой защищённый энд-пойнт | Заголовок `accessToken: <token>` |

---

## Роуты

### Пользователь
| Запрос | Метод | Параметры | Ответ |
| --- | --- | --- | --- |
| `/user/profile` | `GET` | — | Текущий пользователь |
| `/user/purchases` | `GET` | — | История покупок текущего пользователя |

### Продукты
| Запрос | Метод | Параметры | Ответ |
| --- | --- | --- | --- |
| `/product` | `GET` | `?category=` | Каталог |
| `/product/{id}` | `GET` | — | Карточка |
| `/product/buy` | `POST` | `{"product_id":…,"qty":…}` | Покупка |

### Ивенты (src/api/events.py)
| Запрос | Метод | Параметры | Тело | Ответ |
| --- | --- | --- | --- | --- |
| `/event/current` | `GET` | — | — | Список активных ивентов |
| `/event/result` | `POST` | `?event_id` | число — результат | `{ "updated":bool,"result":float,"place":int }` |
| `/event/leaderboard` | `GET` | `?event_id` `?limit=30` | — | `{ top[], current_user }` |

### Призы (src/api/prizes.py)
| Запрос | Метод | Тело/URL | Ответ |
| --- | --- | --- | --- |
| `/prizes/unclaimed` | `GET` | — | Незабранные призы |
| `/prizes/claim` | `POST` | `{"prize_id":…}` | `{ "claimed":true }` |

### Система (src/api/system.py)
| Запрос | Метод | Параметры | Ответ |
| --- | --- | --- | --- |
| `/system/time` | `GET` | — | `{ "utc_time": "2025-01-01T00:00:00+00:00" }` |

---

## Схемы DTO

### Event
```jsonc
{
  "id": 17,
  "name": "Weekend Cup",
  "event_type": "max",
  "start_date": "2025-07-12T00:00:00Z",
  "end_date":   "2025-07-14T00:00:00Z",
  "prizes": [ { "place": 1, "rewards": 100 }, … ]
}
```
UnclaimedReward
```
{
  "reward_id": 55,
  "event_id": 17,
  "place": 4,
  "rewards": 25,
  "created": "2025-07-14T00:05:00Z"
}
```


| Вопрос                                            | Ответ                                               |
| ------------------------------------------------- | --------------------------------------------------- |
| Как получить токен?                               | `POST /auth/login` → accessToken                    |
| Несколько активных ивентов?                       | Сначала `/event/current`, выбираем `id`             |
| Как сравниваются результаты?                      | Поле `event_type`: `max` (больше = лучше) или `min` |
| Предел TOP-N?                                     | Параметр `limit` (≥1, по умолчанию 30)              |
| Как узнать, есть ли приз?                         | Если `/prizes/unclaimed` пуст — всё забрано         |
| Что вернёт `/event/result`, если шлём второй раз? | `"updated": true`, `result` — финальное             |


| Код | Случай                                                   |
| --- | -------------------------------------------------------- |
| 400 | Неверные данные / неактивный ивент / неверный `prize_id` |
| 401 | Токен нет или истёк                                      |
| 404 | Ивент / приз / пользователь не найден                    |




python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
Swagger: http://localhost:8000/docs



СОЗДАТЬ ИВЕНТ
```sql
INSERT INTO public.events (
  name,
  event_type,
  logo,
  start_date,
  end_date,
  level_ids
) VALUES (
  'Тестовый ивент',
  'demo',
  'https://example.com/placeholder.png',  -- здесь указываете свой URL/путь
  NOW() - INTERVAL '3 hour',
  NOW() + INTERVAL '1 hour',
  '[1,2]'::json
);
```

ДОБАВИТЬ ПРИЗЫ ЗА ИВЕНТ
```sql
INSERT INTO event_prizes (event_id, place, rewards)
VALUES
  (1, 1, '[{"gold":"1000", "skin":"epic_crown"}]'),
  (1, 2, '[{"gold":"500"}]'),
  (1, 3, '[{"gold":"300"}]'),
  (1, 4, '[{"gold":"200"}]'),
  (1, 5, '[{"gold":"100"}]');
```