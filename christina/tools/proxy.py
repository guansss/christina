import json
import os
from subprocess import Popen, PIPE, call

from pydantic import BaseModel

CONFIG_FILE = '/etc/shadowsocks-libev/config.json'
CONFIG_TMP = '/tmp/ssconfig.tmp'

HTTP_PROXY = os.environ['PROXY']


class ProxyConfig(BaseModel):
    server: str


def get_proxy_config() -> ProxyConfig:
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    return ProxyConfig(**config)


def set_proxy_config(proxy: ProxyConfig):
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    config['server'] = proxy.server

    with open(CONFIG_TMP, 'w') as f:
        json.dump(config, f, indent=4)

    call(['sudo', 'mv', CONFIG_TMP, CONFIG_FILE])

    restart_service()


def restart_service():
    p = Popen(['sudo', 'systemctl', 'restart', 'shadowsocks-libev-local@config'], stdout=PIPE, stderr=PIPE)

    output, error = p.communicate()

    if p.returncode != 0:
        raise ChildProcessError(f'Execution failed with code {p.returncode}. Details:\n{output}\n{error}')
