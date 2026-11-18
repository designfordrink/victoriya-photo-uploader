# Victoriya Photo Uploader

Проект помощника для подготовки фотографий платьев к публикации на сайте салона Victoriya.

## Development process

Разработка ведётся по регламенту **Standard Project Development Pipeline — Github Stage-Gated**:

Discovery → PRD → TRD → Detailed Specification → Implementation Plan → Implementation → Integration / QA → Release → Post-Release.

Следующая стадия начинается только после принятия результата предыдущей стадии.

## Current stage

**Stage 0 — Discovery**

Основной сценарий первого помощника: пользователь передаёт публичную ссылку на платье производителя; агент находит и скачивает доступные фотографии, подготавливает главное фото 600 × 800 и дополнительные изображения размером не более 2.5 MB, затем сохраняет результат в локальную папку.

Подробности и открытые вопросы: [Discovery Report](docs/discovery/discovery-report.md).

## Project principles

- Original downloaded images are never overwritten.
- The AI may choose the image-processing method automatically, but must report exceptions and uncertain results.
- Product photography may only be processed and published within the salon's usage permissions.
- No bypassing logins, paywalls, anti-bot controls, or other access restrictions.
- Technical checks and human acceptance are separate gates.
