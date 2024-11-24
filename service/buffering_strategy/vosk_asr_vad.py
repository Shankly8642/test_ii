import asyncio
import json
import os
import time
from .buffering_strategy_interface import BufferingStrategyInterface


class VoskAsrVad(BufferingStrategyInterface):
    """
    Стратегия буферизации, которая активируется по ключевой фразе и завершает
    запись по истечении 60 секунд или при паузе в 1.5 секунды.
    """

    def __init__(self, client, **kwargs):
        """
        Инициализация стратегии буферизации.

        Аргументы:
            client (Client): Экземпляр клиента.
            **kwargs: Дополнительные параметры.
        """
        self.client = client

        self.activation_timeout_seconds = kwargs.get("activation_timeout_seconds", 60)
        self.silence_timeout_seconds = kwargs.get("silence_timeout_seconds", 1.5)
        self.activation_keywords = kwargs.get(
            "activation_keywords", ["мульти", "мультиварка", "мультиварочка"]
        )

        self.recording = False
        self.last_voice_activity = time.time()
        self.processing_flag = False

    def process_audio(self, websocket, vad_pipeline, asr_pipeline):
        """
        Обрабатывает аудиоданные, управляя записью и транскрипцией.

        Аргументы:
            websocket: Веб-сокет для отправки результатов транскрипции.
            vad_pipeline: Конвейер для детекции голосовой активности.
            asr_pipeline: Конвейер для автоматического распознавания речи.
        """
        if self.processing_flag:
            return

        # Проверяем наличие голосовой активности
        asyncio.create_task(self.handle_audio(websocket, vad_pipeline, asr_pipeline))

    async def handle_audio(self, websocket, vad_pipeline, asr_pipeline):
        """
        Управляет записью и транскрипцией в зависимости от голосовой активности.

        Аргументы:
            websocket: Веб-сокет для отправки результатов транскрипции.
            vad_pipeline: Конвейер для детекции голосовой активности.
            asr_pipeline: Конвейер для автоматического распознавания речи.
        """
        vad_results = await vad_pipeline.detect_activity(self.client)
        if not vad_results:
            if self.recording and time.time() - self.last_voice_activity > self.silence_timeout_seconds:
                # Заканчиваем запись по истечении времени тишины
                await self.complete_recording(websocket, asr_pipeline)
            return

        # Проверяем, есть ли ключевые слова в результатах
        for segment in vad_results:
            if any(keyword in segment.get("text", "").lower() for keyword in self.activation_keywords):
                self.recording = True
                self.last_voice_activity = time.time()

        if self.recording:
            self.client.scratch_buffer += self.client.buffer
            self.client.buffer.clear()
            self.last_voice_activity = time.time()

            # Завершаем запись, если накоплено более 60 секунд
            if len(self.client.scratch_buffer) / (
                self.client.sampling_rate * self.client.samples_width
            ) > self.activation_timeout_seconds:
                await self.complete_recording(websocket, asr_pipeline)

    async def complete_recording(self, websocket, asr_pipeline):
        """
        Завершает запись и выполняет транскрипцию.

        Аргументы:
            websocket: Веб-сокет для отправки результатов транскрипции.
            asr_pipeline: Конвейер для автоматического распознавания речи.
        """
        self.processing_flag = True
        transcription = await asr_pipeline.transcribe(self.client)

        if transcription["text"]:
            transcription["processing_time"] = time.time() - self.last_voice_activity
            await websocket.send(json.dumps(transcription))

        # Сброс состояния
        self.client.scratch_buffer.clear()
        self.client.increment_file_counter()
        self.recording = False
        self.processing_flag = False
