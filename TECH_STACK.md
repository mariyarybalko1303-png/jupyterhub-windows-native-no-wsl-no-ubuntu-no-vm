# Нативне розгортання JupyterHub на Windows (без WSL2, Ubuntu та віртуальних машин)

Повний посібник, стек технологій, журнал термінальних команд та робоча конфігурація для нативного запуску **JupyterHub** у Windows PowerShell без підсистеми WSL, сторонніх дистрибутивів Linux чи гіпервізорів.

---

## 1. Стек технологій та інструменти

* **PowerShell (v5.1 / v7+):** системне керування, політики виконання скриптів (`ExecutionPolicy`), навігація та робота з процесами.
* **Python (v3.13):** середовище запуску сервера JupyterHub, сесій користувачів (`jupyterhub.singleuser`), ядра `ipykernel` та вебінтерфейсу JupyterLab.
* **Node.js (v24.x) / npm:** середовище для роботи системного зворотного проксі `configurable-http-proxy`.
* **pywinpty & terminado:** підтримка емуляції терміналів Windows у вебінтерфейсі JupyterLab.

---

## 2. Повний покроковий журнал команд (PowerShell)

### Етап 1: Підготовка Node.js та проксі-сервера
```powershell
# Перевірка наявності середовища Node.js
node -v
npm -v

# Зняття блокування запуску скриптів PowerShell (виправлення PSSecurityException)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Глобальне встановлення Configurable HTTP Proxy через npm
npm install -g configurable-http-proxy

# Перевірка працездатності встановленого проксі
configurable-http-proxy --version
```

### Етап 2: Створення та активація віртуального середовища Python
```powershell
# Створення робочого каталогу проєкту
New-Item -ItemType Directory -Path "C:\jupyterhub" -Force
Set-Location -Path "C:\jupyterhub"

# Створення віртуального середовища Python 3.13
python -m venv venv

# Активація віртуального середовища у PowerShell
.\venv\Scripts\Activate.ps1
```

### Етап 3: Встановлення JupyterHub та компонентів
```powershell
# Оновлення базових менеджерів пакетів
python -m pip install --upgrade pip setuptools wheel

# Встановлення JupyterHub, JupyterLab, pywinpty та terminado
pip install jupyterhub jupyterlab pywinpty terminado
```

### Етап 4: Генерація та запуск конфігурації
```powershell
# Генерація базового конфігураційного файлу
jupyterhub --generate-config -f jupyterhub_config.py

# Відкриття конфігурації у текстовому редакторі
notepad jupyterhub_config.py

# Запуск сервера у режимі детальної діагностики (Debug)
jupyterhub -f jupyterhub_config.py --debug

# Штатний запуск сервера для щоденної роботи
jupyterhub -f jupyterhub_config.py
```

---

## 3. Готова конфігурація (jupyterhub_config.py)

Вміст файлу `C:\jupyterhub\jupyterhub_config.py` з усіма адаптаціями під Windows:

```python
import sys
import os
import asyncio
from jupyterhub.spawner import SimpleLocalProcessSpawner

# 1. Фікс циклу подій для Windows (запобігає зависанню веб-сокетів)
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 2. Кастомний спавнер для обходу несумісних викликів POSIX у Windows
class WindowsSpawner(SimpleLocalProcessSpawner):
    def make_preexec_fn(self, name):
        # Відключаємо preexec_fn, який викликає ValueError у Windows subprocess
        return None

    def get_env(self):
        # Передаємо системні змінні оточення Windows дочірньому процесу
        env = super().get_env()
        env.update(os.environ)
        return env

c.JupyterHub.spawner_class = WindowsSpawner

# 3. Прямий виклик однокористувацького сервера через інтерпретатор із venv
c.Spawner.cmd = [sys.executable, '-m', 'jupyterhub.singleuser']
c.Spawner.ip = '127.0.0.1'

# 4. Нормалізований шлях до робочої папки (прямі слеші запобігають помилці Traitlets)
c.Spawner.notebook_dir = 'C:/jupyterhub/notebooks'
c.Spawner.default_url = '/lab'

# 5. Збільшені таймаути на старт процесів у Windows
c.Spawner.start_timeout = 180
c.Spawner.http_timeout = 180

# 6. Явне призначення PowerShell оболонкою для веб-термінала
c.Spawner.args = [
    '--ServerApp.terminado_settings={"shell_command": ["powershell.exe"]}'
]

# 7. Базова автентифікація для локального тестування
c.JupyterHub.authenticator_class = 'dummy'
c.DummyAuthenticator.password = "secret123"

# 8. Мережеві налаштування хабу та проксі
c.JupyterHub.bind_url = 'http://127.0.0.1:8000'
c.JupyterHub.hub_ip = '127.0.0.1'
c.JupyterHub.hub_port = 8081
```

---

## 4. Автоматичний запуск як служба Windows та автентифікація

### Налаштування автозапуску через NSSM (Non-Sucking Service Manager)

Для забезпечення безперебійної роботи JupyterHub у фоновому режимі без відкритої сесії PowerShell рекомендується розгортання через системну службу Windows за допомогою інструменту **NSSM**:

```powershell
# Завантаження та встановлення NSSM через winget
winget install NSSM.NSSM

# Створення нової служби Windows з назвою JupyterHub
nssm install JupyterHub "C:\jupyterhub\venv\Scripts\python.exe" "-m jupyterhub -f C:\jupyterhub\jupyterhub_config.py"

# Налаштування робочого каталогу служби
nssm set JupyterHub AppDirectory "C:\jupyterhub"

# Налаштування автоматичного перезапуску при збоях
nssm set JupyterHub AppExit Default Restart

# Запуск служби JupyterHub
Start-Service JupyterHub

# Перевірка статусу служби
Get-Service JupyterHub
```

### Конфігурація автентифікації користувачів

Для переходу від тестового модуля `DummyAuthenticator` до повноцінного захисту доступу використовуються наступні рішення:

1. **Native Authenticator (Локальні облікові записи):**
   ```python
   # Реєстрація та авторизація локальних користувачів
   c.JupyterHub.authenticator_class = 'nativeauthenticator.NativeAuthenticator'
   c.NativeAuthenticator.open_signup = False  # Контрольоване додавання користувачів
   ```

2. **LDAP / Active Directory Authenticator (Корпоративне середовище):**
   ```python
   # Інтеграція з Active Directory через ldapauthenticator
   c.JupyterHub.authenticator_class = 'ldapauthenticator.LDAPAuthenticator'
   c.LDAPAuthenticator.server_address = 'ldaps://ad.yourcompany.com'
   c.LDAPAuthenticator.bind_dn_template = ['DOMAIN\\{username}']
   ```

---

## 5. Підсумкова таблиця налаштувань та розв'язання проблем (Quick Reference)

| Компонент / Проблема | Опис та причина у Windows | Рішення / Налаштування у конфігурації |
| :--- | :--- | :--- |
| **`PSSecurityException`** | Заблоковано запуск `.ps1` скриптів активації `venv`. | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **`preexec_fn` ValueError** | Взяття Linux-функцій у `subprocess` під час спавну процесу. | `make_preexec_fn` повертає `None` у кастомному `WindowsSpawner`. |
| **Зависання WebSockets** | Несумісність стандартного `ProactorEventLoop` з проксі. | `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` |
| **Спецсимволи у шляхах** | Помилка парсингу зворотних слешів `\` у `Traitlets`. | Використання прямих слешів у шляху (`C:/jupyterhub/notebooks`). |
| **Запуск SingleUser** | Спроба виклику неіснуючих POSIX-команд оточення. | `c.Spawner.cmd = [sys.executable, '-m', 'jupyterhub.singleuser']` |
| **Емуляція термінала** | За замовчуванням використовуються Linux shell або `cmd.exe`. | `terminado_settings={"shell_command": ["powershell.exe"]}` |
| **Затримка запуску** | Триваліший старт процесів Python/JupyterLab у Windows. | Збільшення таймаутів: `c.Spawner.start_timeout = 180`. |
| **Фоновий запуск** | Закриття вікна PowerShell завершує процес JupyterHub. | Конфігурація системної служби Windows через **NSSM**. |
