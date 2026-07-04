# AppSec Middle+ Trainer

Практический тренажёр для подготовки Middle+ AppSec Engineer. Контентная база генерируется из `appsec_middle_plus_trainer.md`, а продуктовая логика следует концепту из `AppSec Middle+ Trainer Concept.pdf`.

## Возможности

- Dashboard с общим прогрессом, уровнем, streak, confidence и weak areas.
- Каталог тем: SSDLC, DAST, API Security, Fuzzing, SAST, SCA, Containers, Kubernetes, Threat Modeling, CI/CD Gates, Triage, Interview.
- Несколько типов заданий: single choice, true/false, theory, practical, scenario, lab, interview.
- Разбор expected answer и red flags после ответа.
- Авторизация с защитой от brute force на login.
- Регистрация обычных пользователей через UI.
- Серверное хранение прогресса по пользователям.
- Админский reset прогресса выбранного пользователя.
- Confidence - самооценка уверенности в ответе, чтобы отличать осознанное знание от угадывания.
- API-фильтры по `topic`, `level` и `type`.

## Запуск локально

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Открой `http://localhost:8080`.

## Пользователи

Перед первым запуском создай `.env` на базе `.env.example`:

```bash
SECRET_KEY=change-me-to-a-random-long-value
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strong-admin-password
```

При первом запуске создаётся `data/users.json` с админом из `.env`. Обычные пользователи создаются через кнопку "Регистрация" на странице входа.

Login защищён лимитом `10 per minute` и lockout после `5` неудачных попыток на `10` минут. Настройки: `MAX_LOGIN_FAILURES`, `LOCKOUT_MINUTES`.

Админская вкладка доступна только пользователю с ролью `admin`; там можно сбросить прогресс выбранному пользователю.

## Генерация контента

```bash
python scripts/generate_trainer_content.py "C:\Users\dioni\Downloads\appsec_middle_plus_trainer.md" static
```

Генератор создаёт:

- `static/trainer_content.json` - полная база тем и заданий для нового UI.
- `static/questions.json` - совместимый массив заданий для `/api/questions`.

## API

- `GET /api/content` - темы и задания.
- `GET /api/questions` - только задания.
- `GET /api/progress` - прогресс текущего пользователя.
- `PUT /api/progress` - сохранить прогресс текущего пользователя.
- `GET /api/admin/users` - список пользователей для admin.
- `POST /api/admin/reset-progress` - сброс прогресса пользователя для admin.
- Query params: `topic`, `level` или `difficulty`, `type`.

Пример:

```text
/api/content?topic=dast&type=case
```

## Docker

```bash
docker build -t appsec-middle-trainer .
docker volume create appsec-middle-data
docker run -d \
  --name appsec-middle-trainer \
  -p 8080:8080 \
  -e SECRET_KEY="change-me-to-a-random-long-value" \
  -e ADMIN_USERNAME="admin" \
  -e ADMIN_PASSWORD="strong-admin-password" \
  -v appsec-middle-data:/app/data \
  appsec-middle-trainer
```

Для локального запуска можно использовать `.env`, но в Docker/на сервере лучше передавать переменные окружения через `docker run`, compose или секреты CI/CD. Файл `.env` и `data/users.json` не коммитятся.

Проверка:

```bash
curl http://localhost:8080/healthz
```
