# Установка rcssserver (и rcssmonitor) на macOS

Для лабораторной нужны **сервер** (rcssserver) и по желанию **монитор** (rcssmonitor) для визуализации. Ниже — установка через Homebrew и сборку из исходников.

---

## Вариант 1: Только сервер (минимум для проверки агентов)

Агенты подключаются к серверу и выводят координаты в консоль. Монитор не обязателен.

### 1. Установите Xcode Command Line Tools (если ещё нет)

```bash
xcode-select --install
```

### 2. Установите зависимости

**Homebrew:** autotools для сборки, Boost — см. ниже.

```bash
brew install autoconf automake libtool
brew install boost   # для сборки rcssserver нужна версия с libboost_system (см. шаг 3)
```

**Важно:** в Boost 1.89+ библиотеки `libboost_system` нет (она стала header-only). Если при configure появится ошибка «Could not find Boost::System», поставьте старую Boost (см. раздел «Если что-то пошло не так» внизу).

### 3. Скачайте и соберите rcssserver

**Способ A — через git (надёжно):**

```bash
cd ~/Downloads   # или любая папка
git clone https://github.com/rcsoccersim/rcssserver.git rcssserver-src
cd rcssserver-src
git fetch --tags
# Последний релиз (теги бывают 16.0.0 или release-16.0.0 и т.п.)
LATEST=$(git describe --tags $(git rev-list --tags --max-count=1) 2>/dev/null || echo "master")
git checkout "$LATEST"
./bootstrap
# Новые версии требуют C++17; на Mac задаём clang++ и пути к Boost (Homebrew)
BREW_PREFIX=$(brew --prefix)
./configure CXX=clang++ CXXFLAGS='-std=c++17' \
  CPPFLAGS="-I$BREW_PREFIX/include" LDFLAGS="-L$BREW_PREFIX/lib"
make
sudo make install
```

Если тегов в репозитории нет, соберите с ветки по умолчанию: `git checkout master` (или `main`), затем те же `./bootstrap`, `./configure`, `make`.

**Способ B — curl + tar (если git не хотите использовать):**

```bash
cd ~/Downloads
# -L обязательно (следовать редиректам), иначе скачается HTML
curl -L https://github.com/rcsoccersim/rcssserver/archive/refs/tags/16.0.0.tar.gz -o rcssserver.tar.gz
# Проверка: архив должен быть не меньше ~1 MB и не HTML
file rcssserver.tar.gz
# Должно быть: rcssserver.tar.gz: gzip compressed data...
# Если видите "HTML document" — удалите файл и используйте способ A (git)
tar xzf rcssserver.tar.gz
cd rcssserver-16.0.0
./bootstrap
./configure CXX=clang++ CXXFLAGS='-std=c++17'
make
sudo make install
```

Если `./bootstrap` нет или падает, попробуйте сразу `./configure CXX=clang++ CXXFLAGS='-std=c++17'` и затем `make`.

### 4. Запуск сервера

```bash
rcssserver
```

При первом запуске в `~/.rcssserver/` создадутся конфиги. Дальше в других терминалах запускайте агентов (см. README в lab1).

---

## Вариант 2: Сервер + монитор (с визуализацией поля)

Монитор зависит от Qt. На современных Mac часто проще ставить зависимости через **MacPorts** (как в старых гайдах), потому что для rcssmonitor традиционно используют Qt4.

### Зависимости (MacPorts)

Установите MacPorts: <https://www.macports.org/install.php>

```bash
sudo port install boost pkgconfig
sudo port install qt4-mac    # или qt5, если в проекте есть поддержка
```

### Сборка rcssserver (как в варианте 1)

```bash
cd rcssserver-16.0.0
./configure CXXFLAGS='-std=c++14'
make
sudo make install
```

### Сборка rcssmonitor

```bash
cd ~/Downloads
curl -L -o rcssmonitor.tar.gz https://github.com/rcsoccersim/rcssmonitor/archive/refs/tags/16.0.0.tar.gz
tar xzf rcssmonitor.tar.gz
cd rcssmonitor-16.0.0
./bootstrap
./configure CXXFLAGS='-std=c++14'
make
sudo make install
```

Если при `./configure` ругается на отсутствие Qt, укажите путь к Qt (пример для MacPorts Qt4):

```bash
export PATH="/opt/local/libexec/qt4/bin:$PATH"
./configure CXXFLAGS='-std=c++14'
```

### Запуск

```bash
# Терминал 1
rcssserver

# Терминал 2
rcssmonitor
```

В мониторе: меню → Kick off / Play on.

---

## Если что-то пошло не так

- **«Could not find a version of the Boost::System library»** — в Boost 1.89+ библиотеки `libboost_system` нет. Нужна Boost 1.84–1.88.

  **Вариант А:** проверьте, есть ли старая версия в Homebrew: `brew search boost` (ищите `boost@1.84` или аналог). Если есть: `brew install boost@1.84`, затем:
  ```bash
  BREW_PREFIX=$(brew --prefix boost@1.84)
  ./configure CXX=clang++ CXXFLAGS='-std=c++17' CPPFLAGS="-I$BREW_PREFIX/include" LDFLAGS="-L$BREW_PREFIX/lib"
  ```

  **Вариант Б:** собрать Boost 1.84 вручную и указать путь:
  ```bash
  cd ~/Downloads
  curl -L -o boost_1_84_0.tar.bz2 https://archives.boost.io/release/1.84.0/source/boost_1_84_0.tar.bz2
  tar xjf boost_1_84_0.tar.bz2
  cd boost_1_84_0
  ./bootstrap.sh --prefix=$HOME/opt/boost-1.84
  ./b2 --prefix=$HOME/opt/boost-1.84 -j4 install
  ```
  Затем в каталоге rcssserver:
  ```bash
  ./configure CXX=clang++ CXXFLAGS='-std=c++17' \
    CPPFLAGS="-I$HOME/opt/boost-1.84/include" LDFLAGS="-L$HOME/opt/boost-1.84/lib"
  make
  sudo make install
  ```
- **«A compiler with support for C++17 language features is required»** — на Mac укажите clang++ и стандарт: `./configure CXX=clang++ CXXFLAGS='-std=c++17'`. Если не поможет, поставьте новый GCC: `brew install gcc` и затем `./configure CXX=g++-13 CXXFLAGS='-std=c++17'` (номер может быть g++-12 и т.д., смотрите `ls $(brew --prefix)/bin/g++*`).
- **«autoreconf: command not found»** — нужны autotools: `brew install autoconf automake libtool`, затем снова `./bootstrap`.
- **«tar: Error opening archive: Unrecognized archive format»** — скачался не архив, а HTML (часто из‑за редиректа без `-L` у curl). Удалите файл (`rm rcssserver.tar.gz`) и используйте **способ A (git)** из шага 3 выше.
- **«configure: error»** — смотрите сообщение: не хватает библиотеки (boost, flex, bison). Установите через `brew install boost flex bison` или через MacPorts.
- **«ld: library not found»** после `make install` — иногда помогает:
  ```bash
  sudo mkdir -p /usr/local/lib
  sudo ln -s /opt/homebrew/lib/libboost_*.dylib /usr/local/lib/   # для Apple Silicon
  ```
  или добавить в `~/.zshrc`: `export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"`.
- **Монитор не собирается** — можно работать только с сервером: запустить `rcssserver`, потом агентов; координаты будут в консоли.

Актуальные ссылки на релизы:  
<https://github.com/rcsoccersim/rcssserver/releases>  
<https://github.com/rcsoccersim/rcssmonitor/releases>
