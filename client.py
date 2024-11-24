# isort: skip_file

from service.buffering_strategy.buffering_strategy_factory import (
    BufferingStrategyFactory,
)


class Client:
    """
    Представляет клиента, подключенного к серверу VoiceStreamAI.

    Этот класс поддерживает состояние для каждого подключенного клиента, включая
    их уникальный идентификатор, аудиобуфер, конфигурацию и счетчик обработанных
    аудиофайлов.

    Атрибуты:
        client_id (str): Уникальный идентификатор клиента.
        buffer (bytearray): Буфер для хранения входящих аудиоданных.
        config (dict): Настройки конфигурации клиента, такие как длина фрагмента
                       и смещение.
        file_counter (int): Счетчик обработанных аудиофайлов.
        total_samples (int): Общее количество аудиосэмплов, полученных от
                             данного клиента.
        sampling_rate (int): Частота дискретизации аудиоданных в Гц.
        samples_width (int): Ширина каждого аудиосэмпла в битах.
    """

    def __init__(self, client_id, sampling_rate, samples_width):
        self.client_id = client_id
        self.buffer = bytearray()
        self.scratch_buffer = bytearray()
        self.config = {
            "language": None,
            "processing_strategy": "realtime_vosk_transcribe",  # realtime_vosk_transcribe
            "processing_args": {
                "chunk_length_seconds": 5,
                "chunk_offset_seconds": 0.1,
            },
        }
        self.file_counter = 0
        self.total_samples = 0
        self.sampling_rate = sampling_rate
        self.samples_width = samples_width
        self.buffering_strategy = (
            BufferingStrategyFactory.create_buffering_strategy(
                self.config["processing_strategy"],
                self,
                **self.config["processing_args"],
            )
        )

    def update_config(self, config_data):
        """
        Обновляет конфигурацию клиента.

        Параметры:
            config_data (dict): Новый набор параметров конфигурации.
        """
        self.config.update(config_data)
        self.buffering_strategy = (
            BufferingStrategyFactory.create_buffering_strategy(
                self.config["processing_strategy"],
                self,
                **self.config["processing_args"],
            )
        )

    def append_audio_data(self, audio_data):
        """
        Добавляет аудиоданные в буфер клиента.

        Параметры:
            audio_data (bytes): Входящие аудиоданные.
        """
        self.buffer.extend(audio_data)
        self.total_samples += len(audio_data) / self.samples_width

    def clear_buffer(self):
        """
        Очищает основной буфер клиента.
        """
        self.buffer.clear()

    def increment_file_counter(self):
        """
        Увеличивает счетчик обработанных аудиофайлов.
        """
        self.file_counter += 1

    def get_file_name(self):
        """
        Генерирует имя файла для текущего аудиофайла.

        Возвращает:
            str: Имя файла в формате "{client_id}_{file_counter}.wav".
        """
        return f"{self.client_id}_{self.file_counter}.wav"

    def process_audio(self, websocket, vad_pipline, asr_pipeline):
        """
        Обрабатывает аудиоданные, используя заданную стратегию буферизации.

        Параметры:
            websocket: Веб-сокет для отправки результатов обработки.
            asr_pipeline: Конвейер автоматического распознавания речи (ASR).
        """
        self.buffering_strategy.process_audio(
            websocket, vad_pipline, asr_pipeline
        )
