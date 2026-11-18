# Stage 4 — Implementation Plan
## Victoriya Photo Assistant — MVP 1

**Статус:** ACCEPTED — Gate 4 принят владельцем продукта 18 ноября 2026  
**Версия:** 0.1  
**Дата:** 18 ноября 2026  
**Discovery:** [Stage 0 — Discovery Report](../discovery/discovery-report.md) — ACCEPTED  
**PRD:** [Stage 1 — PRD v0.1](../prd/prd-v0.1.md) — ACCEPTED  
**TRD:** [Stage 2 — TRD v0.1](../trd/trd-v0.1.md) — ACCEPTED  
**Detailed Specification:** [Stage 3 — Detailed Specification v0.1](../specification/detailed-specification-v0.1.md) — ACCEPTED  
**Репозиторий:** https://github.com/designfordrink/victoriya-photo-uploader  
**Регламент:** [Standard Project Development Pipeline — Github Stage-Gated](https://app.notion.com/p/Standard-Project-Development-Pipeline-Github-Stage-Gated-3f1937a9fdd181dbb1bae975bd77c4f7)

---

## 1. Назначение

Этот план переводит принятую подробную спецификацию в последовательность небольших задач разработки.

Цель — получить локально работающий Victoriya Photo Assistant MVP, который принимает публичную ссылку на платье, получает фотографии, выбирает главное изображение, проверяет каждую фотографию на watermark, подготавливает главное и дополнительные фото, сохраняет файлы и возвращает отчёт.

Работы ведутся короткими независимыми ветками и Pull Request. Каждая часть должна иметь тесты и проверяемый результат. Нельзя начинать следующую крупную часть, если предыдущая не проходит свои критерии готовности.

**В рамках Stage 4 код не пишется.** После принятия этого плана можно переходить к Stage 5 — Implementation.

## 2. Общая стратегия реализации

Разработка ведётся снизу вверх — от безопасных и измеряемых операций к AI-операциям:

1. Скелет Python-проекта, настройки, безопасность локальных файлов и структура задания.
2. Детерминированная обработка изображений и манифест.
3. Получение публичной галереи через Playwright.
4. Подключение Jev 1.14: оценка фотографий и проверка наличия watermark.
5. Кадрирование и простое расширение фона.
6. Отдельные адаптеры Stability Outpaint и Erase/Inpaint с тестами на реальных разрешённых фото.
7. Подготовка дополнительных изображений, итоговая проверка и отчёт.
8. Локальный MCP-сервер и навык Hermes.
9. Сквозной пилот на нескольких моделях платьев, исправления и выпуск MVP.

Платные AI-вызовы не используются в обычных unit-тестах. Для них создаются интерфейсы, тестовые ответы (fixtures) и mock-серверы. Реальные API-вызовы включаются только на интеграционных и пилотных шагах.

## 3. Предлагаемая структура репозитория

Структура уточняется при создании первых файлов, но должна сохранять разделение компонентов:

```text
victoriya-photo-uploader/
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env.example
├── config/
│   └── config.example.yaml
├── docs/
│   ├── discovery/
│   ├── prd/
│   ├── trd/
│   ├── research/
│   ├── specification/
│   └── implementation/
├── src/
│   └── victoriya_photo/
│       ├── __init__.py
│       ├── config/
│       ├── domain/
│       ├── jobs/
│       ├── collector/
│       ├── images/
│       │   ├── normalize.py
│       │   ├── crop.py
│       │   ├── background.py
│       │   ├── watermark/
│       │   └── optimize.py
│       ├── models/
│       │   ├── openrouter.py
│       │   ├── jev.py
│       │   └── stability.py
│       ├── storage/
│       ├── reporting/
│       ├── mcp_server/
│       └── cli.py
├── hermes/
│   └── skills/
│       └── victoriya-photo-assistant/
│           └── SKILL.md
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
└── scripts/
```

Actual product photos, downloaded manufacturer files, API responses containing proprietary images, credentials and local job workspaces must not be committed to the public repository. Test images should be synthetic, public-domain, or explicitly cleared for repository distribution. Private salon test samples stay outside Git.

## 4. Общие правила разработки

### 4.1. Технологическая база

- Python: выбрать актуальную стабильную версию, совместимую с Hermes tooling, Playwright, Pillow, OpenCV и используемыми моделями; закрепить версию в проекте до первого кода.
- Управление зависимостями: `uv` и `pyproject.toml`; `uv.lock` коммитится.
- Тесты: pytest.
- Проверки качества: Ruff (lint/format) и Pyright или mypy (типизация); выбрать один type checker в Task 0.
- Автоматические проверки GitHub Actions: установка, lint, type check, unit tests.
- Внешние API: через отдельные интерфейсы и конфигурацию; в unit tests — только mocks/fakes.
- Изображения: Pillow как основной детерминированный инструмент; OpenCV добавлять только там, где он реально нужен.
- Playwright: Chromium, установленный командой проекта, версия браузера закрепляется lock/config.
- Все операции с файлами должны быть ограничены настроенной корневой папкой `Victoriya`.

### 4.2. Правила GitHub

- Каждая задача или небольшой логически связанный набор задач — отдельная ветка от `main`.
- Pull Request должен ссылаться на Task ID из этого плана.
- Все PR включают описание изменений, тесты и критерии приёмки.
- Нельзя объединять PR с падающими обязательными проверками.
- Документация обновляется вместе с изменением поведения.
- Не коммитить `.env`, API-ключи, cookies, реальные исходники производителей, локальные логи и готовые фотографии.
- До принятия Implementation Plan не создавать продуктовый код; после принятия план может быть превращён в GitHub Issues.

### 4.3. Definition of Done для каждой задачи

Задача считается готовой, если:
- выполнены все пункты её acceptance criteria;
- есть автоматические тесты для новой логики;
- ошибки имеют понятные коды/сообщения;
- не нарушены ограничения безопасности и сохранения оригиналов;
- lint, type check и обязательные тесты проходят;
- README/документы обновлены, если изменился пользовательский сценарий или настройка;
- PR проверен и объединён в `main`.

## 5. Этапы и задачи разработки

### Phase 0 — Bootstrap и безопасная основа

**Цель:** создать минимальный Python-проект и гарантировать, что последующие задачи не смогут случайно затронуть чужие файлы.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-001 | Создать структуру Python package и `pyproject.toml` | Проект устанавливается локально, есть CLI entry point | Нет |
| IMP-002 | Настроить тесты, lint, type check и GitHub Actions | CI проверяет каждый PR | IMP-001 |
| IMP-003 | Добавить config loader и проверку конфигурации | Читается локальный YAML, обязательные поля проверяются | IMP-001 |
| IMP-004 | Реализовать безопасный Path Manager | Все пути остаются внутри `Victoriya root`; path traversal и symlink escape запрещены | IMP-003 |
| IMP-005 | Добавить шаблоны `.env.example`, `config.example.yaml`, `.gitignore` | Секреты и локальные фото защищены от коммита | IMP-001 |

**Gate P0:**
- проект устанавливается на Windows;
- команда проверки и pytest запускаются;
- CI проходит;
- неверный или отсутствующий `Victoriya root` выдаёт понятную ошибку;
- тесты подтверждают, что запись за пределами root невозможна.

### Phase 1 — Domain model, jobs, storage и manifest

**Цель:** реализовать жизненный цикл задания независимо от браузера и AI.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-006 | Описать Pydantic/domain схемы PhotoJob, Asset, ProductIdentity, WatermarkResult, ProcessingResult | Типизированные структуры данных | IMP-001 |
| IMP-007 | Реализовать Job Repository и генерацию job_id | Задание создаётся, читается и обновляется | IMP-006 |
| IMP-008 | Реализовать Job State Machine | Допустимые переходы статусов проверяются кодом | IMP-006 |
| IMP-009 | Реализовать Source/Output/Work/Reports Storage Manager | Каталоги создаются по утверждённой структуре | IMP-004, IMP-007 |
| IMP-010 | Реализовать JSON manifest и Markdown report writer | Состояние каждого asset сохраняется | IMP-006–IMP-009 |
| IMP-011 | Реализовать SHA-256, exact deduplication и no-overwrite policy | Оригиналы не меняются; существующие output не перезаписываются | IMP-009 |

**Gate P1:**
- тестируется полный жизненный цикл задания без сети;
- manifest сериализуется и читается обратно;
- одинаковый SHA-256 не создаёт дубликат;
- существующий файл никогда не перезаписывается;
- исходный hash остаётся прежним после любых тестовых операций.

### Phase 2 — Базовая обработка изображений

**Цель:** обеспечить точные операции с файлами до подключения AI.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-012 | Реализовать безопасный image loader | Только валидные изображения, ограничение размера и защита от повреждённых файлов | IMP-001 |
| IMP-013 | Реализовать EXIF orientation и RGB normalization | Нормализованная копия без изменения source | IMP-012 |
| IMP-014 | Реализовать format converter | WebP/PNG/другие поддерживаемые форматы → JPG | IMP-013 |
| IMP-015 | Реализовать геометрические функции 3:4 и crop planner | Рассчитывается окно 600×800 без растяжения | IMP-013 |
| IMP-016 | Реализовать deterministic crop с защитным bounding box | Crop запрещается, если модель/платье выходит за окно | IMP-015 |
| IMP-017 | Реализовать secondary image optimizer | JPG ≤2 500 000 bytes, пропорции сохраняются | IMP-014 |
| IMP-018 | Реализовать output validator | Проверяет формат, точный размер, вес, декодирование и hash | IMP-014–IMP-017 |

**Gate P2:**
- набор unit fixtures проходит конвертацию;
- главное тестовое изображение сохраняется ровно 600×800;
- secondary image всегда меньше/равен 2 500 000 bytes или получает честный validation error;
- исходники byte-for-byte не меняются;
- crop test подтверждает, что запрещённое окно не обрезает заданный bounding box.

### Phase 3 — Product Page Collector

**Цель:** научиться получать реальные изображения из публичных страниц производителей.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-019 | Реализовать URL parser и SSRF guards | Запрещены private IP, localhost, небезопасные redirects и схемы | IMP-001 |
| IMP-020 | Создать Playwright browser manager | Изолированный Chromium context, timeout и чистая сессия | IMP-019 |
| IMP-021 | Реализовать generic gallery discovery | Сбор `img/src/srcset`, alt, порядок и URL из DOM | IMP-020 |
| IMP-022 | Добавить lazy-loading handling | Скролл и открытие публичных миниатюр | IMP-021 |
| IMP-023 | Реализовать downloader с лимитами и MIME/decode validation | Оригиналы скачиваются в source/job_id | IMP-019, IMP-021 |
| IMP-024 | Реализовать gallery filtering и deduplication | Исключаются логотипы, баннеры, миниатюры и точные дубликаты | IMP-011, IMP-023 |
| IMP-025 | Добавить site adapter для Pronovias | Точечная поддержка контрольной страницы SUFI | IMP-021–IMP-024 |
| IMP-026 | Добавить generic fallback adapter и error reporting | Незнакомая структура сайта не приводит к ложному успеху | IMP-021–IMP-024 |

**Gate P3:**
- публичная страница SUFI загружает галерею и скачивает доступные изображения;
- тестовая страница с lazy loading обрабатывается;
- блокировка доступа возвращает ACCESS_RESTRICTED;
- collector не обращается к localhost/private IP при redirect;
- количество найденных/скачанных/пропущенных файлов отражается в job record.

### Phase 4 — OpenRouter и Jev 1.14

**Цель:** подключить структурированные визуальные решения и откалибровать поведение на реальных фотографиях.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-027 | Реализовать OpenRouter HTTP client, retry, timeout и error mapping | Общий API-клиент без раскрытия ключей | IMP-003 |
| IMP-028 | Реализовать Jev Decisions adapter и типизированный parser | Noul/Choice/Score/Box работают через `typesafe/jev-1.14` | IMP-027 |
| IMP-029 | Подготовить контактные листы и asset previews | Изображения получают стабильные asset_id | IMP-013, IMP-023 |
| IMP-030 | Реализовать lead-photo scoring | Оцениваются фронтальность, полный рост, видимость платья и резкость | IMP-028, IMP-029 |
| IMP-031 | Реализовать watermark Noul для каждого изображения | Каждый asset получает absent/present/uncertain | IMP-028, IMP-029 |
| IMP-032 | Реализовать uncertain recheck по перекрывающимся тайлам | Неопределённость не приводит к удалению | IMP-031 |
| IMP-033 | Реализовать confidence/usage logging и calibration report | Ошибки классификации и стоимость видны в отчёте | IMP-028–IMP-032 |
| IMP-034 | Проверить Gemini escalation adapter | Резервная модель вызывается только по правилам эскалации | IMP-027, IMP-030–IMP-032 |

**Gate P4:**
- тестовые Jev responses разбираются без вызовов сети;
- изображения без watermark не запускают дальнейший watermark pipeline;
- uncertain не запускает Erase;
- lead photo выбирается по заданным критериям;
- pilot labels позволяют посчитать false positives и false negatives;
- OpenRouter API key не попадает в Git, отчёты и логи.

### Phase 5 — Watermark mask и cleanup

**Цель:** удалять watermark только в подтверждённых случаях и не менять остальную фотографию.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-035 | Реализовать Jev Box localization | Координаты watermark и confidence | IMP-028, IMP-031 |
| IMP-036 | Реализовать PaddleOCR text polygons adapter | Контуры букв внутри ROI | IMP-035 |
| IMP-037 | Протестировать SAM 2 mask adapter для графического watermark | Pixel mask для logo cases, если качество достаточное | IMP-035 |
| IMP-038 | Реализовать mask composer/validator | Маска соответствует размеру, не пуста и не закрывает запрещённые области | IMP-036, IMP-037 |
| IMP-039 | Реализовать Stability AI Erase adapter | Запрос на удаление с маской | IMP-027, IMP-038 |
| IMP-040 | Реализовать optional Stability AI Inpaint adapter | Удаление с текстовым указанием восстановления | IMP-027, IMP-038 |
| IMP-041 | Реализовать source-preserving compositor | Вне маски исходные пиксели остаются неизменными | IMP-012, IMP-038–IMP-040 |
| IMP-042 | Реализовать post-cleanup verification | Остаточный watermark и артефакты фиксируются | IMP-041, IMP-031 |

**Gate P5:**
- фотографии без watermark полностью пропускают Box/OCR/SAM/Erase/Inpaint;
- подтверждённый watermark на простом фоне удаляется в рамках маски;
- тест с watermark на кружеве переводится в NEEDS_REVIEW, если маска или восстановление небезопасны;
- вне маски сохраняется исходный пиксельный контент;
- при ошибке внешнего API оригинал не теряется и не объявляется очищенным.

### Phase 6 — Crop / Outpaint и главное фото

**Цель:** получить главное фото 600×800 с сохранением исходного платья.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-043 | Реализовать subject bounding box/keep-out region | Защитная область модели и платья | IMP-028–IMP-030 |
| IMP-044 | Реализовать flat-background extension | Локальное расширение простого фона | IMP-015, IMP-043 |
| IMP-045 | Реализовать Stability AI Outpaint adapter | Сложный фон расширяется слева/справа | IMP-027, IMP-043 |
| IMP-046 | Реализовать source-preserving outpaint compositor | Оригинал сохраняется в центре; смешивается только фон | IMP-045 |
| IMP-047 | Реализовать main-photo processor | Автоматический выбор crop/flat extension/outpaint | IMP-016, IMP-044–IMP-046 |
| IMP-048 | Реализовать visual/geometry quality checks | Ошибки стыков, срезы модели и unsafe edge случаи отмечаются | IMP-043, IMP-047 |
| IMP-049 | Реализовать main output validation | JPG, 600×800, корректный профиль и декодирование | IMP-018, IMP-047 |

**Gate P6:**
- идеальный фронтальный full-length кадр выбирается при его наличии;
- если первый кадр не подходит, выбирается лучший альтернативный;
- crop не отрезает голову, ноги, платье и шлейф;
- расширение фона не изменяет исходные пиксели модели/платья;
- source frame уже обрезан — задача помечается для проверки, части платья не генерируются;
- результат валиден как JPG ровно 600×800.

### Phase 7 — Orchestration, secondary pipeline и отчёт

**Цель:** объединить все готовые модули в один вызов подготовки.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-050 | Реализовать `prepare_product_images` orchestration service | Запуск lead/watermark/secondary pipeline по одному job_id | IMP-030–IMP-049 |
| IMP-051 | Реализовать retry/idempotency/cost cache | Повторный запуск не дублирует файлы и платные вызовы | IMP-007, IMP-010, IMP-050 |
| IMP-052 | Реализовать summary и job report | JSON + Markdown отчёт с файлами, методами, usage и warnings | IMP-010, IMP-050 |
| IMP-053 | Реализовать partial-result rules | Частичный успех не маскируется под полный | IMP-008, IMP-050, IMP-052 |
| IMP-054 | Реализовать output naming/collision handling | `<Model>-main.jpg`, numbered secondary, suffix при конфликте | IMP-009, IMP-050 |

**Gate P7:**
- задание по job_id выполняется повторяемо;
- все asset records имеют watermark status и processing result;
- файл не попадает в successful outputs без успешной проверки;
- финальный отчёт совпадает с фактическим содержимым output directory.

### Phase 8 — MCP и Hermes Desktop

**Цель:** сделать интерфейс «передал ссылку — получил фотографии».

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-055 | Создать локальный MCP server stdio | Сервер запускается как дочерний процесс | IMP-006–IMP-010 |
| IMP-056 | Экспортировать `discover_product_gallery` | Hermes может создать job и получить скачанную галерею | IMP-019–IMP-026, IMP-055 |
| IMP-057 | Экспортировать `prepare_product_images` | Hermes запускает автономную подготовку job | IMP-050, IMP-055 |
| IMP-058 | Экспортировать `get_photo_job_report` | Hermes получает полный статус и путь к output | IMP-052, IMP-055 |
| IMP-059 | Создать Hermes Skill `Victoriya Photo Assistant` | Инструкция задаёт правильную последовательность трёх инструментов | IMP-056–IMP-058 |
| IMP-060 | Подготовить установку на Windows и troubleshooting | Пошаговая установка, конфигурация и диагностика | IMP-055–IMP-059 |

**Gate P8:**
- Hermes через OpenRouter вызывает MCP-инструменты без ручного запуска команд пользователем;
- повторное сообщение с тем же job_id не запускает дублирующую обработку;
- отсутствующий локальный путь и API key дают понятные сообщения;
- MCP не предоставляет произвольный shell или общий доступ ко всему диску.

### Phase 9 — End-to-end pilot, QA и release candidate

**Цель:** проверить полный сценарий на разрешённых публичных фотографиях реальных платьев.

| ID | Задача | Результат | Зависимости |
|---|---|---|---|
| IMP-061 | Подготовить приватный labelled test set | Подборка no-watermark, text/logo/translucent watermark, сложного фона и разных ракурсов | IMP-029 |
| IMP-062 | Выполнить watermark calibration | Отчёт Jev false positive/false negative и выбранные пороги | IMP-031–IMP-038, IMP-061 |
| IMP-063 | Выполнить outpaint/erase quality benchmark | Сравнение качества и стоимости Stability/local вариантов | IMP-039–IMP-049, IMP-061 |
| IMP-064 | Выполнить SUFI end-to-end pilot | Полный путь URL → output → report | IMP-055–IMP-060 |
| IMP-065 | Выполнить pilot на 3–5 других публичных моделях | Проверка разных галерей и композиций | IMP-064 |
| IMP-066 | Исправить ошибки и закрыть regression tests | Повторяемый тестовый набор | IMP-061–IMP-065 |
| IMP-067 | Подготовить Release Candidate и инструкцию запуска | Версия MVP для ежедневного тестового использования | IMP-066 |

**Gate P9:**
- главные фото для всех тестовых jobs соответствуют JPG 600×800;
- все secondary outputs ≤2 500 000 bytes;
- фотографии без watermark не отправляются на удаление;
- спорные случаи честно отмечаются;
- исходники сохраняются;
- результаты визуально приняты владельцем/сотрудником салона;
- стоимость и время каждого job видны в отчёте;
- README и инструкции соответствуют фактической реализации.

## 6. Критический путь и зависимости

Критический путь разработки:

```text
Bootstrap
  |
  v
Config + Secure Storage + Job Manifest
  |
  v
Image Normalization + Deterministic Processing
  |
  v
Playwright Collector
  |
  v
Jev Adapter + Lead Selection + Watermark Noul
  |
  +-----------------------+
  |                       |
  v                       v
Mask / Erase           Crop / Outpaint
  |                       |
  +-----------+-----------+
              |
              v
      Orchestration + Report
              |
              v
       MCP Tools + Hermes Skill
              |
              v
         E2E Pilot + QA
              |
              v
         Release Candidate
```

Некоторые задачи могут выполняться параллельно после появления контрактов и базовых тестов:
- маски watermark и main photo geometry;
- MCP server skeleton и image pipeline;
- documentation/installer и regression suite.

Не выполнять параллельно работу над одним файлом/модулем без предварительного согласования владельца этого файла.

## 7. Стратегия тестирования

### 7.1. Unit tests

Без сетевых вызовов:
- URL validation и SSRF checks;
- нормализация EXIF и форматов;
- crop calculations;
- byte-size optimization;
- manifest serialization;
- job transitions;
- watermark branching logic;
- mask geometry and validation;
- path containment;
- source hash preservation;
- no-overwrite и idempotency.

### 7.2. Integration tests

С моками или тестовыми ответами:
- Playwright collector adapters;
- OpenRouter Jev Noul/Box parser;
- Stability Outpaint/Erase response parsing;
- MCP tool contracts;
- job storage/report pipeline.

Реальные API integration tests запускаются вручную или в отдельном защищённом workflow; их ключи не должны быть доступны обычным fork PR.

### 7.3. End-to-end tests

Контрольные случаи:
1. Нет watermark ни на одной фотографии.
2. Watermark есть на одной фотографии из галереи.
3. Неуверенное watermark решение.
4. Текстовый watermark на простом фоне.
5. Графический watermark.
6. Watermark на кружеве — автоматическое удаление запрещено при небезопасной маске.
7. Первое фото подходит для главного превью.
8. Первое фото не подходит, следующее подходит.
9. Все фото неидеальны — выбрать fallback.
10. Узкая фотография с ровным фоном.
11. Узкая фотография со сложным фоном.
12. Исходное фото уже обрезает платье.
13. Вторичные изображения требуют сжатия.
14. Существующий файл output не перезаписывается.
15. Повторный запуск одного job не вызывает платные операции повторно без причины.

## 8. Управление расходами

- Все AI вызовы проходят через адаптеры с единым учётом usage.
- Jev Noul запускается на каждой фотографии; Box/OCR/SAM/Erase — только в подтверждённых watermark cases.
- Для отбора кандидатов использовать уменьшенные previews/contact sheets, а не пересылать полные оригиналы без необходимости.
- Stability Outpaint вызывается только когда Crop/простое локальное расширение не подходят.
- Stability Erase вызывается только после положительного Noul и проверки маски.
- Платные тесты отделены от CI.
- Перед запуском реального pilot выводить прогнозируемые операции и установленный spending limit; превышение лимита запрещает новые облачные вызовы.
- Фиксировать provider, model, endpoint, tokens/credits и фактическую стоимость в job report, если провайдер её возвращает.

## 9. Безопасность и работа с тестовыми фотографиями

- Репозиторий публичный: реальные фотографии производителей и полученные от брендов материалы не добавлять в Git без отдельного явного разрешения на распространение.
- Приватный тестовый набор размещается в локальной папке вне репозитория.
- API keys хранятся в локальном secret storage / environment.
- `.env` и локальные config не коммитятся.
- Все выходные пути остаются внутри `Victoriya root`.
- Фото отправляются в OpenRouter/Stability только в рамках включённой cloud policy.
- Публичный сайт производителя не обходится при наличии ограничения доступа.

## 10. Рекомендуемая последовательность Pull Requests

| PR | Содержание | Основные задачи |
|---|---|---|
| PR-01 | Python bootstrap, CI, config, safe paths | IMP-001–005 |
| PR-02 | Job domain, state machine, storage, manifest | IMP-006–011 |
| PR-03 | Image loader, normalize, crop, JPG optimizer, validation | IMP-012–018 |
| PR-04 | URL safety, Playwright collector, gallery download | IMP-019–026 |
| PR-05 | OpenRouter + Jev adapter, lead selection, watermark detection | IMP-027–034 |
| PR-06 | Jev Box, OCR/SAM masks, Erase/Inpaint adapter, compositor | IMP-035–042 |
| PR-07 | Background extension, Outpaint, lead image processing | IMP-043–049 |
| PR-08 | Full pipeline orchestration, idempotency, reports | IMP-050–054 |
| PR-09 | MCP server and Hermes skill | IMP-055–060 |
| PR-10 | Pilot, calibration, QA, Release Candidate | IMP-061–067 |

PR-06 и PR-07 могут идти параллельно после принятия API/масочных контрактов. Их интеграция выполняется в PR-08.

## 11. Что нужно подготовить до реализации

Следующие ресурсы не требуют изменения архитектуры, но должны быть доступны к соответствующим задачам:

1. Windows-компьютер, на котором будет установлен Hermes Desktop.
2. Полный локальный путь к папке `Victoriya`.
3. OpenRouter API key с бюджетным лимитом.
4. Stability AI API key — только если выбран cloud image processing и салон разрешает передачу изображений.
5. 30 фото без watermark и не менее 15 с watermark для калибровки Jev; по возможности примеры логотипов, прозрачных watermark и надписей на ткани.
6. 5 сложных примеров с watermark на кружеве/вышивке для проверки безопасной остановки.
7. Несколько фотографий для теста Crop и расширения бокового фона.
8. Подтверждение прав на использование и редактирование всех тестовых фотографий.

Тестовый набор хранится отдельно от публичного GitHub-репозитория.

## 12. Измерение результата

Текущая база: примерно 5 платьев в неделю и 10–15 минут ручной работы на одно платье (около 50–75 минут в неделю).

В пилоте измерять:
- время от отправки URL до готовой папки;
- время, которое человек тратит на итоговую проверку;
- число полностью готовых jobs;
- количество fallback main photos;
- Jev false positive/false negative;
- количество безопасно остановленных watermark cases;
- качество outpainting и erase после визуальной проверки;
- количество повторных платных API-вызовов;
- стоимость одного задания;
- долю файлов, потребовавших ручной правки.

Не объявлять экономию времени до реального сравнения с текущим процессом.

## 13. Gate 4 — Implementation Plan Acceptance

| Критерий | Статус |
|---|---|
| Все PRD/Specification requirements разбиты на задачи | Accepted |
| Зависимости и критический путь определены | Accepted |
| Стратегия тестирования определена | Accepted |
| Правила GitHub и Definition of Done определены | Accepted |
| Платные API отделены от обычного CI | Accepted |
| Безопасность фото/секретов учтена | Accepted |
| Пилот и release criteria определены | Accepted |
| Открытые ресурсы для реализации перечислены | Accepted |

**Gate 4 status: ACCEPTED владельцем продукта 18 ноября 2026.**

Stage 4 принят. Можно начинать **Stage 5 — Implementation**, начиная с PR-01 (bootstrap, CI и безопасная конфигурация). Каждая последующая часть остаётся отдельной проверяемой задачей и Pull Request.
