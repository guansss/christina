import json
import os

from pydantic import BaseModel

from christina import utils

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

    utils.subprocess(['sudo', 'mv', CONFIG_TMP, CONFIG_FILE])

    restart_service()


def restart_service():
    utils.subprocess('sudo systemctl restart shadowsocks-libev-local@config')
