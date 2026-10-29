# Dependency Graph Visualizer (Variant 25)

## Описание
CLI-приложение для визуализации графа зависимостей.
Этап 1: Чтение конфигурации из YAML, валидация параметров и вывод в формате ключ-значение.

## Установка
pip install pyyaml

## Запуск
py src/main.py --config config.yaml

## Тестирование ошибок
py src/main.py --config bad_config.yaml