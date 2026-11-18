# PR-01 — Bootstrap: запуск и локальная конфигурация

## Требования
- Windows 10/11 x64 или актуальный Windows с Python 3.12.
- Установленный uv.
- Доступ к репозиторию GitHub.

## Первоначальная установка

```powershell
git clone https://github.com/designfordrink/victoriya-photo-uploader.git
cd victoriya-photo-uploader
uv sync --all-groups
# If uv.lock was not present, uv creates it during the first sync.
uv lock
Copy-Item config/config.example.yaml config/config.yaml
```

Открой `config/config.yaml` и укажи полный путь к папке данных:

```yaml
paths:
  victoriya_root: 'D:/Victoriya'
```

Либо используй переменную среды `VICTORIYA_ROOT` как переопределение. Файл `config/config.yaml` не добавляется в Git.

Если `uv.lock` был создан впервые, добавь его в репозиторий вместе с изменениями зависимостей:

```powershell
git add uv.lock
git commit -m "chore: add uv dependency lock"
```

В CI lock-файл создаётся и сохраняется как артефакт, чтобы установка проверялась на Windows и Ubuntu.

## Проверка установки

```powershell
uv run victoriya-photo doctor
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/victoriya_photo
```

Команда `doctor` проверяет YAML-настройки и доступ на запись в папку `Victoriya`. Она создаёт папку, если её ещё нет, записывает временный тестовый файл и сразу удаляет его.

## Секреты

API-ключи не хранятся в YAML и не коммитятся в репозиторий. Для будущих интеграций используй переменные среды:
- `OPENROUTER_API_KEY`;
- `STABILITY_API_KEY`.

На этом этапе сетевые AI-вызовы ещё не реализованы.
