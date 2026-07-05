import json
import hashlib
import re
import sys
from pathlib import Path


DEFAULT_SOURCE = Path(r"C:\Users\dioni\Downloads\appsec_middle_plus_trainer.md")
DEFAULT_EXTRA_SOURCE = Path("content/appsec_interview_questions_ru.json")

TOPICS = [
    ("appsec-basics", "AppSec Basics", "Базовые понятия application security, тестирование, уязвимости, криптография и защитные меры.", "middle"),
    ("ssdlc", "SSDLC", "Security requirements, secure design review, release gates and risk acceptance.", "middle"),
    ("risk-ownership", "Risk Ownership", "Риск-ориентированное владение безопасностью продукта, risk register, gates и приоритизация.", "middle+"),
    ("dast", "DAST", "Authenticated scans, API coverage, active/passive testing and evidence.", "middle+"),
    ("api", "API Security", "BOLA, authz, GraphQL, OpenAPI testing and abuse cases.", "middle+"),
    ("fuzzing", "Web/API Fuzzing", "Payload design, boundary values, stateful API fuzzing and safe execution.", "middle"),
    ("sast", "SAST", "Sources, sinks, sanitizers, taint analysis, code review and custom rules.", "middle+"),
    ("sca", "SCA / Supply Chain", "SBOM, CVE triage, reachability, dependency confusion and exceptions.", "middle+"),
    ("container", "Container Security", "Dockerfile hardening, image risk, runtime settings and least privilege.", "middle"),
    ("kubernetes", "Kubernetes Security", "RBAC, NetworkPolicy, securityContext, admission control and runtime detection.", "middle+"),
    ("threat-modeling", "Threat Modeling", "Trust boundaries, DFD, STRIDE, abuse stories and design review questions.", "middle"),
    ("cicd", "CI/CD Security Gates", "Baselines, blocking rules, exceptions, owner, expiry, SLA and delivery-safe gates.", "middle+"),
    ("mobile", "Mobile Security", "Практическое тестирование iOS/Android, хранение секретов, pinning, MASVS и мобильный baseline.", "middle+"),
    ("secrets", "Secrets Management", "Поиск, ротация и предотвращение утечек секретов в коде, CI/CD и артефактах.", "middle+"),
    ("regulatory", "Regulatory Evidence", "Перевод AppSec-рисков в понятные evidence для аудита, банковских и регулируемых сред.", "middle+"),
    ("triage", "Vulnerability Triage", "False positives, exploitability, severity normalization, remediation and SLA.", "middle+"),
    ("interview", "Interview Preparation", "Open-ended Middle+ AppSec interview questions and expected reasoning.", "middle+"),
]

PREFIX_TOPIC = {
    "DAST": "dast",
    "API": "api",
    "FUZZ": "fuzzing",
    "SAST": "sast",
    "SCA": "sca",
    "CONT": "container",
    "KUBE": "kubernetes",
    "TRIAGE": "triage",
    "INT": "interview",
    "LAB": "triage",
    "CASE": "triage",
    "MCQ": "triage",
    "TF": "triage",
}

TYPE_LABELS = {
    "theory": "Theory",
    "practical": "Practical",
    "case": "Scenario",
    "interview": "Interview",
    "single": "Single Choice",
    "multiple": "Multiple Choice",
    "truefalse": "True / False",
    "lab": "Practical Lab",
}

SEED_TASKS = [
    {
        "id": "ssdlc-seed-001",
        "topic": "ssdlc",
        "level": "middle",
        "type": "case",
        "question": "На этапе design review команда показывает поток browser -> API Gateway -> service -> DB. Что должен проверить Middle+ AppSec Engineer?",
        "expectedAnswer": "Нужно определить trust boundaries, модель аутентификации и авторизации, классификацию данных, угрозы по STRIDE, требования ASVS/API Security, логи аудита, обработку ошибок и точки, где должны появиться security gates.",
        "redFlags": "Ограничиться только запуском сканера после разработки или проверкой security headers.",
    },
    {
        "id": "ssdlc-seed-002",
        "topic": "ssdlc",
        "level": "middle+",
        "type": "practical",
        "question": "Какие security requirements нужны для API, которое отдаёт персональные данные?",
        "expectedAnswer": "Нужны object-level authorization, tenant isolation, минимизация данных, аудит доступа, rate limiting, secure error handling, требования к токенам/session, encryption in transit, data retention, logging без PII и regression checks для критичных abuse cases.",
        "redFlags": "Свести требования только к TLS или общему пункту 'должна быть авторизация'.",
    },
    {
        "id": "tm-seed-001",
        "topic": "threat-modeling",
        "level": "middle",
        "type": "theory",
        "question": "Зачем threat modeling нужен до SAST/DAST?",
        "expectedAnswer": "Threat modeling помогает найти архитектурные и бизнес-риски до реализации: trust boundaries, abuse cases, sensitive data flows, authz decisions и критичные компоненты. SAST/DAST проверяют уже код или работающее приложение и не заменяют secure design review.",
        "redFlags": "Считать threat modeling формальностью после релиза или заменять его отчётом сканера.",
    },
    {
        "id": "tm-seed-002",
        "topic": "threat-modeling",
        "level": "middle+",
        "type": "case",
        "question": "Команда добавляет webhook endpoint, который принимает URL callback от клиента. Какие угрозы и контроли нужно обсудить?",
        "expectedAnswer": "Нужно проверить SSRF, spoofing отправителя, replay, excessive retries, data leakage, callback allowlist, подпись событий, idempotency, таймауты, egress restrictions, audit logs и безопасную обработку ошибок.",
        "redFlags": "Проверить только формат URL и не обсуждать egress/private ranges/replay.",
    },
    {
        "id": "cicd-seed-001",
        "topic": "cicd",
        "level": "middle+",
        "type": "case",
        "question": "Когда security gate должен блокировать релиз, а когда достаточно ticket/exception?",
        "expectedAnswer": "Блокировать стоит новые exploitable critical/high риски на exposed assets, секреты в коде, dangerous container/Kubernetes settings и уязвимости без compensating controls. Ticket/exception допустимы для legacy или нерелевантных findings при наличии owner, reason, expiry, SLA и evidence.",
        "redFlags": "Блокировать всё по CVSS без reachability/exposure или, наоборот, разрешать всё через бессрочные исключения.",
    },
    {
        "id": "cicd-seed-002",
        "topic": "cicd",
        "level": "middle",
        "type": "practical",
        "question": "Как внедрить SAST gate, чтобы не остановить delivery из-за legacy findings?",
        "expectedAnswer": "Нужно создать baseline, блокировать только новые high-confidence findings, настроить ownership, SLA, suppression policy with expiry, severity normalization, developer feedback loop и метрики new/fixed findings, MTTR, false positive rate.",
        "redFlags": "Сразу блокировать все существующие findings или навсегда игнорировать legacy.",
    },
]


def clean(value):
    value = re.sub(r"```(?:yaml)?\n?", "", value)
    value = value.replace("```", "")
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


HUMAN_REPLACEMENTS = [
    ("authenticated DAST", "DAST с авторизацией"),
    ("Authenticated DAST", "DAST с авторизацией"),
    ("spider + активное сканирование", "обхода приложения и активного сканирования"),
    ("active scan", "активное сканирование"),
    ("passive scan", "пассивное сканирование"),
    ("endpoints", "эндпоинты"),
    ("endpoint", "эндпоинт"),
    ("headers", "заголовки"),
    ("partial data leakage", "частичные утечки данных"),
    ("error messages", "сообщения об ошибках"),
    ("timing", "время ответа"),
    ("cache", "кэш"),
    ("update/delete/export эндпоинты", "эндпоинты изменения, удаления и экспорта"),
    ("Fix — object-level authorization", "Исправление — проверка прав на уровне объекта"),
    ("ownership/tenant/role", "владельца, тенанта и роли"),
    ("JSON string", "JSON-строки"),
    ("content-type", "Content-Type"),
    ("MIME sniffing", "автоматическое определение типа содержимого браузером"),
    ("abuse cases", "негативные сценарии"),
    ("stateful testing", "тестирование цепочек состояний"),
    ("domain knowledge", "понимание предметной области"),
    ("workflow", "рабочий процесс"),
    ("Logout, delete, irreversible update, payment, notification/email/SMS, account closing, production data mutation, admin разрушающие действия, external integrations, expensive report generation", "Выход из аккаунта, удаление, необратимые изменения, платежи, отправку email/SMS, закрытие аккаунта, изменение production-данных, разрушительные действия администратора, внешние интеграции и тяжёлую генерацию отчётов"),
    ("safe test env, allowlist сценариев, rate limit, test data и manual approval", "безопасное тестовое окружение, список разрешённых сценариев, ограничение частоты запросов, тестовые данные и ручное согласование"),
    ("CVSS/severity", "оценку CVSS и заявленную критичность"),
    ("exploitability", "эксплуатируемость"),
    ("request/response evidence", "доказательства в запросе и ответе"),
    ("finding", "находку"),
    ("findings", "находки"),
    ("owner, reason и expiry", "ответственного, причину и срок действия"),
    ("owner, reason, expiry", "ответственного, причину и срок действия"),
    ("owner", "ответственного"),
    ("scope", "область проверки"),
    ("destructive actions", "разрушающие действия"),
    ("destructive endpoints", "опасные эндпоинты, меняющие данные"),
    ("scanner", "сканер"),
    ("security headers", "защитные HTTP-заголовки"),
    ("authenticated coverage", "покрытие авторизованных сценариев"),
    ("execution context", "контекст выполнения"),
    ("payload", "проверочная нагрузка"),
    ("payloads", "проверочные нагрузки"),
    ("response body", "тело ответа"),
    ("HTTP status", "HTTP-статус"),
    ("request", "запрос"),
    ("response", "ответ"),
    ("backend", "серверной стороне"),
    ("frontend", "клиентской стороне"),
    ("refresh token/login macro", "обновление токена или сценарий входа"),
    ("logout", "выход из аккаунта"),
    ("expiry", "срок действия"),
    ("scan", "сканирование"),
    ("coverage", "покрытие"),
    ("business flows", "бизнес-сценарии"),
    ("authz", "авторизацию"),
    ("auth/API", "авторизацию и API"),
    ("BOLA/IDOR", "BOLA/IDOR"),
    ("low/info", "низкий или информационный риск"),
    ("false positive", "ложное срабатывание"),
    ("true positive", "подтверждённую находку"),
    ("impact", "влияние"),
    ("root cause", "первопричину"),
    ("remediation", "исправление"),
    ("reachability", "достижимость уязвимого кода"),
    ("exposure", "доступность сервиса извне"),
    ("compensating controls", "компенсирующие меры"),
    ("baseline", "базовую линию"),
    ("high-confidence", "надёжно подтверждённые"),
    ("rules", "правила"),
    ("source", "источник данных"),
    ("sink", "опасный вызов"),
    ("sanitizer", "очистку данных"),
    ("sanitizers", "очистку данных"),
    ("wrapper", "обёртку"),
    ("runtime", "во время выполнения"),
    ("test accounts/test data", "тестовые аккаунты и тестовые данные"),
    ("rate limit/concurrency limit", "ограничение частоты и параллельности запросов"),
    ("correlation id", "идентификатор корреляции"),
    ("test window", "согласованное окно тестирования"),
    ("private ranges/metadata endpoints", "частные сетевые диапазоны и metadata-эндпоинты"),
]


def humanize(value):
    if isinstance(value, str):
        result = value
        for old, new in HUMAN_REPLACEMENTS:
            result = result.replace(old, new)
        result = result.replace("эндпоинтs", "эндпоинты")
        result = result.replace("spider + активное сканирование", "обхода приложения и активного сканирования")
        result = result.replace("обычного spider + активное сканирование", "обычного обхода приложения и активного сканирования")
        result = result.replace("из активное сканирование", "из активного сканирования")
        result = result.replace("через активное сканирование", "через активное сканирование")
        result = result.replace("destructive эндпоинты", "опасные эндпоинты, меняющие данные")
        result = result.replace("выход из аккаунта/опасные эндпоинты", "выход из аккаунта и опасные эндпоинты")
        result = result.replace("без учёта выход из аккаунта", "без учёта выхода из аккаунта")
        result = result.replace("срок действия", "срока действия сессии")
        result = result.replace("ролей и разрушающие действия", "ролей и разрушающих действий")
        result = result.replace("для эндпоинты для изменения", "для эндпоинтов изменения")
        result = result.replace("эндпоинты изменения", "эндпоинты для изменения")
        result = result.replace("UI", "интерфейс")
        result = result.replace("High", "высокий риск")
        result = result.replace("Для таких эндпоинты", "Для таких эндпоинтов")
        result = result.replace("изменение production-данных", "изменение боевых данных")
        result = result.replace("reflected XSS", "отражённый XSS")
        result = result.replace("Как triage?", "Как провести разбор?")
        result = result.replace("state A", "состояния A")
        result = result.replace("state D", "состояние D")
        result = result.replace("во клиентской стороне", "на клиентской стороне")
        result = result.replace("клиентской стороне вставляет", "клиентская сторона вставляет")
        result = result.replace("проверочная нагрузка отразился", "проверочная нагрузка отразилась")
        result = result.replace("анализа тело ответа", "анализа тела ответа")
        result = re.sub(r"\s+", " ", result).strip()
        return result
    if isinstance(value, list):
        return [humanize(item) for item in value]
    if isinstance(value, dict):
        preserved = {"id", "topic", "level", "type", "typeLabel", "answer"}
        return {
            key: item if key in preserved else humanize(item)
            for key, item in value.items()
        }
    return value


def field(block, name):
    pattern = rf"\*\*{re.escape(name)}:\*\*\s*(.*?)(?=\n\*\*[A-ZА-ЯЁ][^*\n]+:\*\*|\n---|\Z)"
    match = re.search(pattern, block, flags=re.S)
    return clean(match.group(1)) if match else ""


def choice_card(card_id, topic, question, choices, correct_letter, explain=""):
    letters = ["A", "B", "C", "D"]
    answer_index = letters.index(correct_letter)
    return {
        "id": card_id.lower(),
        "topic": topic,
        "level": "middle",
        "type": "single",
        "typeLabel": TYPE_LABELS["single"],
        "question": clean(question),
        "choices": choices,
        "answer": answer_index,
        "expectedAnswer": choices[answer_index],
        "explain": clean(explain) or f"Правильный ответ: {choices[answer_index]}",
        "redFlags": "",
    }


def parse_structured_cards(text):
    cards = []
    for match in re.finditer(r"^###\s+([A-Z]+-\d{3})(.*?)^(?=###\s+[A-Z]+-\d{3}|##\s+|\Z)", text, flags=re.M | re.S):
        card_id, block = match.groups()
        prefix = card_id.split("-")[0]
        if prefix in {"MCQ"}:
            continue
        question = field(block, "Question")
        expected = field(block, "Expected answer") or field(block, "Решение")
        if not question:
            continue
        raw_type = (field(block, "Type") or "interview").lower()
        card_type = raw_type if raw_type in TYPE_LABELS else "interview"
        cards.append({
            "id": card_id.lower(),
            "topic": PREFIX_TOPIC.get(prefix, "triage"),
            "level": (field(block, "Level") or "middle+").lower(),
            "type": card_type,
            "typeLabel": TYPE_LABELS.get(card_type, card_type.title()),
            "question": question,
            "choices": [],
            "answer": None,
            "expectedAnswer": expected,
            "explain": expected,
            "redFlags": field(block, "Red flags"),
        })
    return cards


def parse_mcq(text):
    cards = []
    section = text[text.find("## 25. Multiple choice questions"):]
    for match in re.finditer(r"###\s+(MCQ-\d{3})(.*?)(?=\n###\s+MCQ-\d{3}|\n##\s+|\Z)", section, flags=re.S):
        card_id, block = match.groups()
        question = field(block, "Question")
        correct = field(block, "Correct").strip().upper()[:1]
        choices = []
        for letter in ["A", "B", "C", "D"]:
            found = re.search(rf"^{letter}\.\s*(.+?)\s*$", block, flags=re.M)
            if found:
                choices.append(clean(found.group(1)))
        if question and correct in "ABCD" and len(choices) == 4:
            cards.append(choice_card(card_id, "triage", question, choices, correct))
    return cards


def parse_true_false(text):
    cards = []
    section_match = re.search(r"## 26\. True / False(.*?)(?=\n##\s+27\.)", text, flags=re.S)
    if not section_match:
        return cards
    rows = [line for line in section_match.group(1).splitlines() if line.startswith("|") and "---" not in line and "Statement" not in line]
    for index, row in enumerate(rows, 1):
        parts = [clean(part) for part in row.strip("|").split("|")]
        if len(parts) < 3:
            continue
        statement, correct, explanation = parts[:3]
        cards.append({
            "id": f"tf-{index:03d}",
            "topic": "triage",
            "level": "middle",
            "type": "truefalse",
            "typeLabel": TYPE_LABELS["truefalse"],
            "question": statement,
            "choices": ["True", "False"],
            "answer": 0 if correct.lower() == "true" else 1,
            "expectedAnswer": correct,
            "explain": explanation,
            "redFlags": "",
        })
    return cards


def parse_labs(text):
    cards = []
    section_match = re.search(r"## 24\. Практические задания для тренажёра(.*?)(?=\n##\s+25\.)", text, flags=re.S)
    if not section_match:
        return cards
    for match in re.finditer(r"###\s+(LAB-\d{3})(?::\s*([^\n]+))?(.*?)(?=\n###\s+LAB-\d{3}:|\n##\s+|\Z)", section_match.group(1), flags=re.S):
        lab_id, lab_title, block = match.groups()
        title = clean(f"{lab_id}: {lab_title}" if lab_title else lab_id)
        input_text = field(block, "Input") or field(block, "Input manifest")
        task = field(block, "Task")
        expected = field(block, "Expected output") or field(block, "Expected answer")
        if "DAST" in title:
            topic = "dast"
        elif "SAST" in title:
            topic = "sast"
        elif "SCA" in title:
            topic = "sca"
        elif "Kubernetes" in title:
            topic = "kubernetes"
        else:
            topic = "triage"
        cards.append({
            "id": lab_id.lower(),
            "topic": topic,
            "level": "middle+",
            "type": "lab",
            "typeLabel": TYPE_LABELS["lab"],
            "question": clean(f"{title}\n\n{input_text}\n\nTask: {task}"),
            "choices": [],
            "answer": None,
            "expectedAnswer": expected,
            "explain": expected,
            "redFlags": "",
        })
    return cards


def parse_cases(text):
    cards = []
    section_match = re.search(r"## 27\. Open-ended кейсы(.*?)(?=\n##\s+28\.)", text, flags=re.S)
    if not section_match:
        return cards
    for match in re.finditer(r"###\s+(CASE-\d{3}):?\s*(.*?)(?=\n###\s+CASE-\d{3}:|\n##\s+|\Z)", section_match.group(1), flags=re.S):
        header, block = match.groups()
        title = clean(header.splitlines()[0])
        scenario = field(block, "Scenario")
        expected = re.sub(r"\*\*[^*]+:\*\*", "", block)
        cards.append({
            "id": title.split(":")[0].lower(),
            "topic": "triage",
            "level": "middle+",
            "type": "case",
            "typeLabel": TYPE_LABELS["case"],
            "question": clean(f"{title}\n\n{scenario}"),
            "choices": [],
            "answer": None,
            "expectedAnswer": clean(expected),
            "explain": clean(expected),
            "redFlags": "",
        })
    return cards


DISTRACTORS = {
    "default": [
        "Ориентироваться только на оценку CVSS без проверки эксплуатируемости и контекста",
        "Считать находку подтверждённой без доказательств в запросе и ответе",
        "Ограничиться проверкой интерфейса и не проверять контроль на серверной стороне",
        "Оформить бессрочное исключение без ответственного, причины и срока действия",
        "Запустить сканер без области проверки, тестовых данных и ограничений опасных действий",
    ],
    "dast": [
        "Запустить активное сканирование по всему приложению без исключений и согласованного окна",
        "Проверить только защитные HTTP-заголовки и не смотреть покрытие авторизованных сценариев",
        "Считать отражённую строку уязвимостью без проверки контекста выполнения",
    ],
    "sast": [
        "Блокировать все старые находки без базовой линии и настройки правил",
        "Считать любой путь от входных данных до опасного вызова подтверждённым без анализа очистки и контекста",
    ],
    "sca": [
        "Блокировать релиз только из-за Critical CVE без проверки достижимости уязвимого кода",
        "Игнорировать транзитивную зависимость без проверки её использования во время выполнения",
    ],
    "kubernetes": [
        "Разрешить привилегированный pod без отдельного принятия риска",
        "Считать NetworkPolicy работающей без проверки поддержки со стороны CNI",
    ],
}

INTERVIEW_RUBRICS = {
    "int-001": [
        "Разделить pipeline на этапы: секреты, SAST, SCA, проверка образов, IaC и DAST/API",
        "Ввести базовую линию для старых находок и блокировать только новые надёжно подтверждённые риски",
        "Настроить ответственных, SLA, процесс исключений и дашборды для команд",
        "Сделать разные gates для внешних критичных сервисов и низкорисковых внутренних сервисов",
    ],
    "int-002": [
        "Настроить источники данных, опасные вызовы и очистку под реальные обёртки фреймворка",
        "Использовать базовую линию, дедупликацию и надёжные правила для блокирующих проверок",
        "Разбирать ложные срабатывания и улучшать собственные правила по обратной связи",
        "Показывать разработчикам первопричину и исправление, а не только строку с находкой",
    ],
    "int-003": [
        "Оценивать эксплуатируемость, доступность сервиса извне, достижимость кода, критичность актива и данные",
        "Отличать техническую критичность от реального бизнес-риска",
        "Приоритизировать исправления по влиянию и вероятности эксплуатации",
        "Оформлять исключения с ответственным, причиной, сроком действия и компенсирующими мерами",
    ],
    "int-004": [
        "Authentication отвечает на вопрос, кто пользователь или сервис",
        "Authorization отвечает, что этому субъекту разрешено делать",
        "Проверки authorization должны быть на backend и на уровне объекта/tenant",
        "BOLA/IDOR возникает, когда authenticated user получает чужой объект без authz check",
    ],
    "int-005": [
        "Новый эксплуатируемый critical/high риск на сервисе, доступном извне",
        "Секреты в коде или артефактах без немедленной ротации",
        "Привилегированный контейнер или Kubernetes workload без обоснования и согласования",
        "Достижимая уязвимая зависимость с публичным эксплойтом и без компенсирующих мер",
    ],
}


def split_expected_answer(text):
    text = clean(text)
    bullet_lines = []
    for line in text.splitlines():
        raw = line.strip()
        if raw.startswith(("-", "*")):
            bullet_lines.append(raw.strip(" -*\t"))
    if bullet_lines:
        lines = bullet_lines
    else:
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
        if len(sentences) >= 2:
            lines = sentences
        else:
            single = sentences[0] if sentences else text
            looks_like_list = single.count(",") >= 2 and not re.search(r"\b(потому что|если|котор|чтобы|оставляя|но|а)\b", single.lower())
            lines = re.split(r";\s+|,\s+", single) if looks_like_list else [single]
    parts = []
    for item in lines:
        item = humanize(clean(item).strip(". "))
        if 12 <= len(item) <= 220 and item not in parts:
            parts.append(item)
    return parts


def keywords_for(label):
    tokens = re.findall(r"[A-Za-zА-Яа-яЁё0-9+/.-]{4,}", label.lower())
    stop = {
        "нужно", "проверить", "которые", "такой", "также", "если", "или",
        "есть", "должен", "должна", "должно", "with", "that", "only",
    }
    return [token for token in tokens if token not in stop][:5]


def enrich_with_rubric_choices(card):
    if card.get("choices"):
        return card
    expected = card.get("expectedAnswer") or card.get("explain") or ""
    correct_options = INTERVIEW_RUBRICS.get(card.get("id"), split_expected_answer(expected))[:5]
    if not correct_options:
        return card

    wrong_options = []
    if card.get("redFlags"):
        wrong_options.append(humanize(clean(card["redFlags"])))
    wrong_options.extend(DISTRACTORS.get(card.get("topic"), []))
    wrong_options.extend(DISTRACTORS["default"])
    wrong_options = [item for item in wrong_options if item not in correct_options]

    choices = correct_options + wrong_options[: max(3, min(4, len(correct_options) + 1))]
    choices = choices[:8]
    # Deterministic shuffle by card id, so regenerated content stays stable.
    choices = sorted(choices, key=lambda value: f"{card['id']}::{value}"[::-1])
    answers = [index for index, value in enumerate(choices) if value in correct_options]

    card["choices"] = choices
    card["answer"] = answers if len(answers) > 1 else answers[0]
    card["type"] = "multiple" if len(answers) > 1 else "single"
    card["typeLabel"] = TYPE_LABELS[card["type"]]
    card["rubric"] = [
        {"label": option, "keywords": keywords_for(option)}
        for option in correct_options
    ]
    return card


def load_extra_cards(path=DEFAULT_EXTRA_SOURCE):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    cards = data.get("questions", data) if isinstance(data, dict) else data
    normalized = []
    for card in cards:
        item = dict(card)
        item.setdefault("level", "middle+")
        item.setdefault("type", "single")
        item.setdefault("typeLabel", TYPE_LABELS.get(item["type"], item["type"].title()))
        item.setdefault("choices", [])
        item.setdefault("answer", None)
        item.setdefault("expectedAnswer", item.get("explain", ""))
        item.setdefault("explain", item.get("expectedAnswer", ""))
        item.setdefault("redFlags", "")
        normalized.append(item)
    return normalized


def shuffle_choice_order(card):
    choices = card.get("choices") or []
    answer = card.get("answer")
    if not choices or answer is None:
        return card

    correct_indexes = set(answer if isinstance(answer, list) else [answer])
    pairs = list(enumerate(choices))
    pairs.sort(
        key=lambda pair: hashlib.sha256(
            f"{card['id']}::{pair[1]}::{pair[0]}".encode("utf-8")
        ).hexdigest()
    )

    card["choices"] = [choice for _, choice in pairs]
    remapped = [
        new_index
        for new_index, (old_index, _) in enumerate(pairs)
        if old_index in correct_indexes
    ]
    card["answer"] = remapped if isinstance(answer, list) else remapped[0]
    return card


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("static")
    text = source.read_text(encoding="utf-8")
    cards = []
    cards.extend(parse_structured_cards(text))
    cards.extend(parse_mcq(text))
    cards.extend(parse_true_false(text))
    cards.extend(parse_labs(text))
    cards.extend(parse_cases(text))
    for task in SEED_TASKS:
        cards.append({
            **task,
            "typeLabel": TYPE_LABELS.get(task["type"], task["type"].title()),
            "choices": [],
            "answer": None,
            "explain": task["expectedAnswer"],
        })
    cards.extend(load_extra_cards())

    seen = set()
    deduped = []
    for card in cards:
        if card["id"] in seen:
            continue
        seen.add(card["id"])
        deduped.append(card)

    deduped = [shuffle_choice_order(humanize(enrich_with_rubric_choices(card))) for card in deduped]

    topic_counts = {topic_id: 0 for topic_id, *_ in TOPICS}
    lab_counts = {topic_id: 0 for topic_id, *_ in TOPICS}
    for card in deduped:
        topic_counts[card["topic"]] = topic_counts.get(card["topic"], 0) + 1
        if card["type"] in {"lab", "case", "practical"}:
            lab_counts[card["topic"]] = lab_counts.get(card["topic"], 0) + 1

    topics = [
        {
            "id": topic_id,
            "title": title,
            "description": description,
            "level": level,
            "questionCount": topic_counts.get(topic_id, 0),
            "caseCount": lab_counts.get(topic_id, 0),
        }
        for topic_id, title, description, level in TOPICS
    ]

    payload = {
        "source": str(source),
        "title": "AppSec Middle+ Trainer",
        "description": "Практический тренажёр для Middle+ AppSec: вопросы, triage, labs, interview mode и risk-based reasoning.",
        "topics": topics,
        "questions": deduped,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "trainer_content.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "questions.json").write_text(json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(deduped)} tasks across {len(topics)} topics")


if __name__ == "__main__":
    main()
