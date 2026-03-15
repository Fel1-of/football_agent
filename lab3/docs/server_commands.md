# Команды взаимодействия с сервером RoboCup 2D

## Подключение и отключение

| Команда | Формат | Пример |
|---------|--------|--------|
| **init** | `(init <TeamName> [(version <Version>)] [(goalie)])` | `(init MyTeam (version 7))` |
| **bye** | `(bye)` | `(bye)` |

Ответ на init: `(init <side> <unum> <play_mode>)` — side: l/r, unum: 1–11.

## Команды за такт (только одна из пяти!)

| Команда | Формат | Ограничения |
|---------|--------|-------------|
| **move** | `(move <x> <y>)` | x: -54..54, y: -32..32 |
| **turn** | `(turn <moment>)` | moment: -180..180° |
| **dash** | `(dash <power>)` | power: -100..100 |
| **kick** | `(kick <power> <direction>)` | power, direction в градусах |
| **catch** | `(catch <direction>)` | Только вратарь, расстояние до мяча < 2 |

## Входящие сообщения

- **see** — `(see <time> <objInfo>+)` — видимые объекты (флаги, мяч, игроки).
- **hear** — `(hear <time> <sender> <message>)` — sender: referee, self, …
- **sense_body** — состояние тела игрока.

Рефери: `play_on`, `kick_off_l/r`, `goal_l/r`, `drop_ball` и т.д.
