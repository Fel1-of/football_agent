# Установка rcssserver (и rcssmonitor) на Ubuntu

Для лабораторной нужны **сервер** (`rcssserver`) и по желанию **монитор** (`rcssmonitor`) для визуализации.

---

## Вариант 1: Только сервер (минимум для проверки агентов)

### 1. Обновите систему и поставьте инструменты сборки

```bash
sudo apt update
sudo apt install -y build-essential git autoconf automake libtool pkg-config
```

### 2. Установите зависимости для rcssserver

```bash
sudo apt install -y libboost-system-dev libboost-thread-dev libboost-filesystem-dev
```

Если на вашей версии Ubuntu пакет `libboost-system-dev` недоступен или `configure` не находит Boost::System, установите полный набор:

```bash
sudo apt install -y libboost-all-dev
```

### 3. Скачайте и соберите rcssserver

```bash
cd ~/Downloads
git clone https://github.com/rcsoccersim/rcssserver.git rcssserver-src
cd rcssserver-src
./bootstrap
./configure CXXFLAGS='-std=c++17'
make -j"$(nproc)"
sudo make install
```

### 4. Запуск сервера

```bash
rcssserver
```

После этого в других терминалах можно запускать агентов из проекта `lab1`.

---

## Вариант 2: Сервер + монитор (с визуализацией поля)

### 1. Установите зависимости монитора (Qt)

```bash
sudo apt update
sudo apt install -y qtbase5-dev qttools5-dev-tools libqt5svg5-dev
```

### 2. Сборка rcssmonitor

```bash
cd ~/Downloads
git clone https://github.com/rcsoccersim/rcssmonitor.git rcssmonitor-src
cd rcssmonitor-src
./bootstrap
./configure CXXFLAGS='-std=c++17'
make -j"$(nproc)"
sudo make install
```

### 3. Запуск сервера и монитора

```bash
# Терминал 1
rcssserver

# Терминал 2
rcssmonitor
```

В мониторе: **Kick off** → **Play on**.

---

## Проверка запуска агентов (lab1)

Из каталога проекта:

```bash
python3 app.py --team teamA --x -15 --y 0 --rotation 20
```

Во втором терминале:

```bash
python3 app.py --team teamB --x 15 --y 0 --rotation 0
```

---

## Частые проблемы

- `autoreconf: command not found`  
Установите autotools: `sudo apt install -y autoconf automake libtool`.

- `configure: error: C++17 ... required`  
Поставьте свежий компилятор: `sudo apt install -y g++` и повторите `./configure CXXFLAGS='-std=c++17'`.

- `Could not find Boost::System`  
Поставьте полный Boost: `sudo apt install -y libboost-all-dev`.

- `rcssserver: command not found` после `make install`  
Проверьте установку в `/usr/local/bin`:
```bash
which rcssserver
ls -l /usr/local/bin/rcssserver
```
Если бинарник есть, но не в `PATH`, добавьте в `~/.bashrc`:
```bash
export PATH="/usr/local/bin:$PATH"
```

Актуальные репозитории:  
<https://github.com/rcsoccersim/rcssserver>  
<https://github.com/rcsoccersim/rcssmonitor>
