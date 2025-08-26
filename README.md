
# AppSec Dojo (Python, Flask)

Duolingo-стайл тренажёр для middle/senior Web AppSec: CSP, CORS, SSRF, браузерные политики, OWASP Top 10, DAST/Fuzzing, архитектурные ревью (Яндекс 360), Java/Spring/PLSQL.

## Запуск локально
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
# http://localhost:8080
```

## Docker
```bash
docker build -t appsec-dojo-py .
docker run --rm -p 8080:8080 appsec-dojo-py
```

## SSDLC
- Строгие заголовки: CSP, HSTS, XFO, Referrer-Policy, COOP/COEP/CORP, nosniff.
- Rate limiting (Flask-Limiter).
- Без внешних CDN; минимум статики.
- Поверхность атаки — только чтение `/api/questions`.
- Готово к DAST/фаззингу в песочнице.

## Добавление вопросов
`static/questions.json` — формат: `id`, `difficulty`, `topic`, `q`, `choices[]`, `a`, `explain`.
