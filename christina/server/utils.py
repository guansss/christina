from fastapi import WebSocket
from websockets.exceptions import ConnectionClosedError
from typing import List, Union
from christina.logger import get_logger
import asyncio

logger = get_logger(__name__)


class ConnectionManager:
    '''
    https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
    '''

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    def broadcast(self, message: Union[str, dict]):
        asyncio.create_task(self.broadcast_async(message))

    async def broadcast_async(self, message: Union[str, dict]):
        try:
            if isinstance(message, str):
                send_method = 'send_text'

                # convert it to JSON format so the client can parse it correctly
                message = f'"{message}"'
            else:
                send_method = 'send_json'

            for connection in self.active_connections:
                try:
                    await getattr(connection, send_method)(message)
                except ConnectionClosedError:
                    self.disconnect(connection)

        except Exception as e:
            logger.error('Could not broadcast message.')
            logger.exception(e)
