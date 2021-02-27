from fastapi import APIRouter

from christina.logger import get_logger
from christina.tools.proxy import get_proxy_config, set_proxy_config, ProxyConfig

logger = get_logger(__name__)

router = APIRouter(prefix='/proxy')


@router.get('')
def route_proxy():
    return get_proxy_config()


@router.put('')
def route_set_proxy(config: ProxyConfig):
    set_proxy_config(config)

    return get_proxy_config()
