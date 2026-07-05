# Деплой на VPS с доменом

Ниже вариант для Ubuntu-сервера, Docker Compose и автоматического HTTPS через Caddy.

## 1. DNS

В панели домена создай DNS-запись:

```text
Type: A
Name: @
Value: IP_ТВОЕГО_VPS
TTL: Auto
```

Если нужен поддомен:

```text
Type: A
Name: appsec
Value: IP_ТВОЕГО_VPS
TTL: Auto
```

После этого домен будет указывать на сервер. Распространение DNS обычно занимает от нескольких минут до нескольких часов.

## 2. Сервер

На чистом Ubuntu VPS:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Открой порты:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 3. Код

```bash
git clone https://github.com/xeeeion/websecTrain.git
cd websecTrain
```

Если деплоишь приватную ветку, сначала запушь ее в GitHub и на сервере сделай `git checkout имя-ветки`.

## 4. Переменные окружения

Создай `.env` на сервере:

```bash
cp .env.example .env
nano .env
```

Минимально заполни:

```text
DOMAIN=example.com
SECRET_KEY=long-random-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strong-admin-password
MAX_LOGIN_FAILURES=5
LOCKOUT_MINUTES=10
ENABLE_HSTS=1
SESSION_COOKIE_SECURE=1
TRUST_PROXY_HEADERS=1
RATELIMIT_STORAGE_URI=memory://
```

Сгенерировать `SECRET_KEY` можно так:

```bash
openssl rand -hex 32
```

Не коммить `.env` и `data/users.json`.

## 5. Запуск

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

Проверка приложения внутри Docker-сети:

```bash
docker compose exec app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read().decode())"
```

Проверка снаружи:

```bash
curl https://example.com/healthz
```

Caddy сам выпустит и обновит TLS-сертификат, если DNS уже указывает на сервер и порты 80/443 доступны.

## 6. Обновление

```bash
git pull
docker compose up -d --build
```

Пользователи и прогресс сохраняются в Docker volume `appsec_data`.

## 7. Полезные команды

```bash
docker compose logs -f app
docker compose logs -f caddy
docker compose restart
docker compose down
docker volume ls
```

## 8. Если Caddy не получает сертификат

Если в логах есть ошибка вида:

```text
lookup acme-v02.api.letsencrypt.org on 8.8.8.8:53: connect: network is unreachable
```

значит Caddy запустился, но контейнер не может выйти в интернет или сделать DNS-запрос. Это проблема сети Docker/VPS, а не Flask-приложения.

Проверь с хоста:

```bash
curl -I https://acme-v02.api.letsencrypt.org/directory
ping -c 3 1.1.1.1
```

Проверь из контейнера:

```bash
docker compose exec caddy nslookup acme-v02.api.letsencrypt.org
docker compose exec caddy wget -S -O- https://acme-v02.api.letsencrypt.org/directory
docker compose exec caddy ip route
```

Текущий `docker-compose.yml` запускает Caddy в `network_mode: host`, поэтому Caddy использует сеть хоста для DNS и выпуска сертификата. Приложение при этом опубликовано только на `127.0.0.1:8000` и не доступно напрямую из интернета.

Если ты вернул Caddy в обычную Docker bridge-сеть и на хосте интернет есть, а в контейнере нет, проверь forwarding/NAT Docker:

```bash
sudo sysctl net.ipv4.ip_forward
sudo iptables -t nat -L POSTROUTING -n -v
sudo iptables -L FORWARD -n -v
sudo systemctl restart docker
docker compose up -d
```

На Ubuntu с UFW часто помогает разрешить маршрутизацию Docker-трафика:

```bash
sudo ufw status verbose
sudo ufw default allow routed
sudo systemctl restart docker
docker compose up -d
```

После исправления сети Caddy сам повторит выпуск сертификата.
