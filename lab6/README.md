# Лабораторная работа 6. Командная игра (11 игроков)

Адаптация `AgentRep/lab6` под стиль текущего репозитория:
- рабочие `.py` файлы находятся в корне `lab6/`;
- точки входа для агента: `app.py` и `player_runner.py`;
- запуск полного матча: `start.sh` или `python3 launch_match.py`.
- архитектура контроллеров переделана под требования Lab 6 из методички (3 уровня иерархии).

## Состав команды (11)

1. `goalie`
2. `defender_top`
3. `defender_center`
4. `defender_bottom`
5. `defender_sweeper`
6. `midfielder_top`
7. `midfielder_center`
8. `midfielder_bottom`
9. `forward_top`
10. `forward_center`
11. `forward_bottom`

## Быстрый запуск

1. Поднять `rcssserver` и `rcssmonitor`.
2. Из каталога `lab6/`:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
3. В `rcssmonitor`: `Kick off` -> `Play on`.

## Ручной запуск одного игрока

```bash
python3 app.py --team teamA --role midfielder_center --side l
```

## Полезные файлы

- `squad_layout.py` — конфигурация ролей и стартовых позиций.
- `player_runner.py` — сборка и запуск одного игрока.
- `control_hierarchy.py` — базовый механизм вызова уровней контроллера.
- `perception_layer.py` — нижний уровень (восприятие мира и предобработка).
- `motion_layer.py` — средний уровень (тактические примитивные действия).
- `strategy_goalkeeper.py` — верхний уровень для вратаря.
- `strategy_defense.py` — верхний уровень для защитников.
- `strategy_offense.py` — верхний уровень для полузащиты/атаки.
- `launch_team.py` — поднимает 11 игроков одной команды.
- `launch_match.py` — поднимает 2 команды (`teamA`/`teamB`).
- `start_team.py`, `start_match.py`, `main.py` — совместимые алиасы для старых команд запуска.

## Что сделано по требованиям Lab 6

- Реализован иерархический контроллер из трех уровней: нижний, средний, верхний.
- Сделаны отдельные стратегические контроллеры для вратаря и полевых игроков.
- Добавлено ограничение против «толпы за мячом»: игрок идет в прессинг только при выгодных условиях, остальные занимают support-позиции.
- Учтены сообщения рефери и reset-логика через единый контракт между уровнями (`command/new_action/say`).
