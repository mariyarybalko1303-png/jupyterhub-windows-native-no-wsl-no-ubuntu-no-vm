import sys
import os
import asyncio
from jupyterhub.spawner import SimpleLocalProcessSpawner

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class WindowsSpawner(SimpleLocalProcessSpawner):
    def make_preexec_fn(self, name):
        return None

    def get_env(self):
        env = super().get_env()
        env.update(os.environ)
        return env

c.JupyterHub.spawner_class = WindowsSpawner

c.Spawner.cmd = [sys.executable, '-m', 'jupyterhub.singleuser']
c.Spawner.ip = '127.0.0.1'

# Використовуємо прямі слеші без подвійного екранування:
c.Spawner.notebook_dir = 'C:/jupyterhub/notebooks'
c.Spawner.default_url = '/lab'

c.Spawner.start_timeout = 180
c.Spawner.http_timeout = 180

c.JupyterHub.authenticator_class = 'dummy'
c.DummyAuthenticator.password = "secret123"

c.JupyterHub.bind_url = 'http://127.0.0.1:8000'
c.JupyterHub.hub_ip = '127.0.0.1'
c.JupyterHub.hub_port = 8081