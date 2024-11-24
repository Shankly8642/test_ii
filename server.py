import json
import logging
import ssl
import uuid

import websockets

from client import Client


class Server:
    """
    Представляет сервер WebSocket для обработки аудиоданных в реальном времени.

    Этот класс управляет подключениями WebSocket, обрабатывает входящие
    аудиоданные и взаимодействует с конвейерами VAD и ASR для детекции
    голосовой активности и распознавания речи.

    Атрибуты:
        asr_pipeline: Экземпляр конвейера для автоматического распознавания речи.
        host (str): Адрес хоста сервера.
        port (int): Порт, на котором сервер принимает подключения.
        sampling_rate (int): Частота дискретизации аудиоданных в Гц.
        samples_width (int): Ширина каждого аудиосэмпла в битах.
        connected_clients (dict): Словарь, сопоставляющий ID клиентов с объектами
                                  Client.
    """

    def __init__(
        self,
        vad_pipline,
        asr_pipeline,
        host="localhost",
        port=8765,
        sampling_rate=16000,
        samples_width=2,
        certfile=None,
        keyfile=None,
    ):
        self.vad_pipline = vad_pipline
        self.asr_pipeline = asr_pipeline
        self.host = host
        self.port = port
        self.sampling_rate = sampling_rate
        self.samples_width = samples_width
        self.certfile = certfile
        self.keyfile = keyfile
        self.connected_clients = {}

    async def handle_audio(self, client, websocket):
        """
        Обрабатывает входящие аудиоданные от клиента.

        Метод ожидает получения сообщений от клиента через WebSocket. Если
        сообщение представляет собой аудиоданные, оно добавляется в буфер
        клиента. Если сообщение является строкой, предполагается, что это
        конфигурационные данные.

        Аргументы:
            client (Client): Объект клиента, отправившего данные.
            websocket: WebSocket-соединение с клиентом.
        """
        while True:
            message = await websocket.recv()

            if isinstance(message, bytes):
                client.append_audio_data(message)
            elif isinstance(message, str):
                config = json.loads(message)
                if config.get("type") == "config":
                    client.update_config(config["data"])
                    logging.debug(f"Updated config: {client.config}")
                    continue
            else:
                print(f"Unexpected message type from {client.client_id}")

            # Синхронная обработка аудиоданных (асинхронность внутри стратегии буферизации)
            client.process_audio(
                websocket, self.vad_pipline, self.asr_pipeline
            )

    async def handle_websocket(self, websocket):
        """
        Управляет WebSocket-соединением с клиентом.

        Метод создает нового клиента, добавляет его в список подключенных
        клиентов, а затем вызывает метод обработки аудио.

        Аргументы:
            websocket: WebSocket-соединение с клиентом.
        """
        client_id = str(uuid.uuid4())
        client = Client(client_id, self.sampling_rate, self.samples_width)
        self.connected_clients[client_id] = client

        print(f"Client {client_id} connected")

        try:
            await self.handle_audio(client, websocket)
        except websockets.ConnectionClosed as e:
            print(f"Connection with {client_id} closed: {e}")
        finally:
            del self.connected_clients[client_id]

    def start(self):
        """
        Запускает сервер WebSocket.

        Если указан файл сертификата, сервер настраивается для работы через
        защищенные соединения (wss). В противном случае сервер принимает
        обычные соединения (ws).
        """
        if self.certfile:
            # Создание SSL-контекста для обеспечения зашифрованных соединений
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            # Загрузка сертификата и закрытого ключа сервера
            ssl_context.load_cert_chain(
                certfile=self.certfile, keyfile=self.keyfile
            )

            print(
                f"WebSocket-сервер готов к приему защищенных соединений на "
                f"{self.host}:{self.port}"
            )

            # Передаем SSL-контекст в функцию serve
            return websockets.serve(
                self.handle_websocket, self.host, self.port, ssl=ssl_context
            )
        else:
            print(
                f"WebSocket-сервер готов к приему соединений на "
                f"{self.host}:{self.port}"
            )
            return websockets.serve(
                self.handle_websocket, self.host, self.port, origins=None  # Разрешить любые источники и отсутствие Origin
            )
