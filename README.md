\# JupyterHub Native on Windows (Without WSL2)



Інструкція та робоча конфігурація для нативного запуску \*\*JupyterHub\*\* у середовищі Windows (PowerShell) без використання WSL, WSL2 чи віртуальних машин.



Офіційно JupyterHub оптимізований під Unix/Linux середовища, тому при спробі запуску на Windows виникають помилки з циклом подій `asyncio`, системним проксі, доступом до виконання скриптів у PowerShell та несумісністю `preexec\_fn` у `subprocess.Popen`. Нижче описано, як обійти ці проблеми.



\---



\## 🛠 Передумови (Prerequisites)



1\. \*\*Python 3.10+\*\* (переконайтеся, що позначено "Add python.exe to PATH").

2\. \*\*Node.js (LTS)\*\* — обов'язковий для запуску зворотного проксі `configurable-http-proxy`.



\---



\## ⚙️ Покрокове встановлення



\### 1. Дозвіл на виконання скриптів у PowerShell

За замовчуванням політика безпеки Windows блокує запуск сценаріїв `npm` та `activate.ps1`. Дозвольте їх виконання для поточного користувача:

```powershell

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

```



\### 2. Встановлення Node.js та проксі-сервера

Встановіть Node.js (якщо ще не встановлено):

```powershell

winget install OpenJS.NodeJS.LTS

```

\*Перезапустіть консоль PowerShell\*, після чого встановіть `configurable-http-proxy`:

```powershell

npm install -g configurable-http-proxy

```



\### 3. Створення віртуального оточення

```powershell

mkdir C:\\jupyterhub

cd C:\\jupyterhub

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



\### 4. Встановлення залежностей Python

```powershell

python -m pip install --upgrade pip

pip install jupyterhub notebook jupyterlab

```



\---



\## 🔧 Конфігурація (`jupyterhub\_config.py`)



Створіть файл `jupyterhub\_config.py` або використайте файл із цього репозиторію.



\### Ключові виправлення для Windows:

1\. \*\*`asyncio.WindowsSelectorEventLoopPolicy`\*\* — запобігає зависанню та збоям циклу подій.

2\. \*\*Кастомний `WindowsSpawner` без `preexec\_fn`\*\* — на Windows параметр `preexec\_fn` у `subprocess.Popen` викликає виняток `ValueError: preexec\_fn is not supported on Windows platforms`.

3\. \*\*Передача `os.environ`\*\* — гарантує, що дочірній процес отримає всі системні шляхи Windows (`PATH`).

4\. \*\*Нормалізація шляху `notebook\_dir`\*\* — прямі слеші (`C:/...`) замість подвійних лапок/бекслешів уникають помилки `TraitError: No such directory`.



```python

import sys

import os

import asyncio

from jupyterhub.spawner import SimpleLocalProcessSpawner



\# 1. Фікс SelectorEventLoop для Windows

if sys.platform.startswith('win'):

&#x20;   asyncio.set\_event\_loop\_policy(asyncio.WindowsSelectorEventLoopPolicy())



\# 2. Спавнер з вимкненим Unix preexec\_fn та передачею системного оточення

class WindowsSpawner(SimpleLocalProcessSpawner):

&#x20;   def make\_preexec\_fn(self, name):

&#x20;       return None



&#x20;   def get\_env(self):

&#x20;       env = super().get\_env()

&#x20;       env.update(os.environ)

&#x20;       return env



c.JupyterHub.spawner\_class = WindowsSpawner



\# 3. Виклик single-user сервера через активний venv

c.Spawner.cmd = \[sys.executable, '-m', 'jupyterhub.singleuser']

c.Spawner.ip = '127.0.0.1'



\# 4. Робоча папка для блокнотів

c.Spawner.notebook\_dir = 'C:/jupyterhub/notebooks'

c.Spawner.default\_url = '/lab'



\# 5. Збільшені таймаути для старту процесів

c.Spawner.start\_timeout = 180

c.Spawner.http\_timeout = 180



\# 6. Автентифікація (Dummy для тестування)

c.JupyterHub.authenticator\_class = 'dummy'

c.DummyAuthenticator.password = "secret123"



\# 7. Мережеві налаштування

c.JupyterHub.bind\_url = '\[http://127.0.0.1:8000](http://127.0.0.1:8000)'

c.JupyterHub.hub\_ip = '127.0.0.1'

c.JupyterHub.hub\_port = 8081

```



Створіть робочу папку для ноутбуків:

```powershell

New-Item -ItemType Directory -Force -Path "C:\\jupyterhub\\notebooks"

```



\---



\## 🚀 Запуск



У вікні PowerShell з активованим `venv`:

```powershell

jupyterhub -f jupyterhub\_config.py

```



\- Відкрийте браузер: `http://127.0.0.1:8000`

\- Вхід: будь-яке ім'я користувача (наприклад, `testuser`)

\- Пароль: `secret123`

