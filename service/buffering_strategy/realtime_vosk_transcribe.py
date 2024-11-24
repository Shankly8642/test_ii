import asyncio
import json
import os
import time

from .buffering_strategy_interface import BufferingStrategyInterface


class RealtimeVoskTranscribe(BufferingStrategyInterface):
    """
    Стратегия буферизации, которая обрабатывает аудиоданные в конце каждого
    фрагмента с использованием детекции тишины.

    Этот класс отвечает за обработку аудиофрагментов, обнаружение тишины в
    конце каждого фрагмента и запуск процесса транскрипции для данного
    фрагмента.

    Атрибуты:
        client (Client): Экземпляр клиента, связанный с данной стратегией
                         буферизации.
        chunk_length_seconds (float): Длина каждого аудиофрагмента в секундах.
        chunk_offset_seconds (float): Временное смещение в секундах, которое
                                      учитывается при обработке аудиофрагментов.
    """

    def __init__(self, client, **kwargs):
        """
        Инициализация стратегии буферизации SilenceAtEndOfChunk.

        Аргументы:
            client (Client): Экземпляр клиента, связанный с данной стратегией
                             буферизации.
            **kwargs: Дополнительные именованные аргументы, включая
                      'chunk_length_seconds' и 'chunk_offset_seconds'.
        """
        self.client = client

        self.chunk_length_seconds = os.environ.get(
            "BUFFERING_CHUNK_LENGTH_SECONDS"
        )
        if not self.chunk_length_seconds:
            self.chunk_length_seconds = kwargs.get("chunk_length_seconds")
        self.chunk_length_seconds = float(self.chunk_length_seconds)

        self.chunk_offset_seconds = os.environ.get(
            "BUFFERING_CHUNK_OFFSET_SECONDS"
        )
        if not self.chunk_offset_seconds:
            self.chunk_offset_seconds = kwargs.get("chunk_offset_seconds")
        self.chunk_offset_seconds = float(self.chunk_offset_seconds)

        self.error_if_not_realtime = os.environ.get("ERROR_IF_NOT_REALTIME")
        if not self.error_if_not_realtime:
            self.error_if_not_realtime = kwargs.get(
                "error_if_not_realtime", False
            )

        self.processing_flag = False

    def process_audio(self, websocket, asr_pipeline):
        """
        Обрабатывает аудиофрагменты, проверяя их длину и планируя асинхронную
        обработку.

        Этот метод проверяет, превышает ли длина буфера аудио длину фрагмента,
        и, если это так, запускает асинхронную обработку аудио.

        Аргументы:
            websocket: Веб-сокет для отправки результатов транскрипции.
            vad_pipeline: Конвейер для детекции голосовой активности.
            asr_pipeline: Конвейер для автоматического распознавания речи.
        """
        chunk_length_in_bytes = (
            self.chunk_length_seconds
            * self.client.sampling_rate
            * self.client.samples_width
        )
        if len(self.client.buffer) > chunk_length_in_bytes:
            if self.processing_flag:
                exit(
                    "Ошибка в режиме реального времени: попытка обработки нового "
                    "фрагмента, пока предыдущий еще обрабатывается."
                )

            self.client.scratch_buffer += self.client.buffer
            self.client.buffer.clear()
            self.processing_flag = True
            # Планируем обработку в отдельной задаче
            asyncio.create_task(
                self.process_audio_async(websocket, asr_pipeline)
            )

    async def process_audio_async(self, websocket, asr_pipeline):
        """
        Асинхронно обрабатывает аудио для детекции активности и транскрипции.

        Этот метод выполняет ресурсоемкую обработку, включая детекцию голосовой
        активности и транскрипцию аудиоданных. Он отправляет результаты
        транскрипции через веб-сокет.

        Аргументы:
            websocket (Websocket): Веб-сокет для отправки результатов
                                   транскрипции.
            vad_pipeline: Конвейер для детекции голосовой активности.
            asr_pipeline: Конвейер для автоматического распознавания речи.
        """
        start = time.time()

        transcription = await asr_pipeline.transcribe(self.client)
        if transcription["text"] != "":
            end = time.time()
            transcription["processing_time"] = end - start
            send_transcription = json.dumps(transcription)
            await websocket.send(send_transcription)
        self.client.scratch_buffer.clear()
        self.client.increment_file_counter()

        self.processing_flag = False
