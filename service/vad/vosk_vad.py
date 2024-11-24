import wave
import json
import os
from vosk import Model as VoskModel, KaldiRecognizer
from utils.audio_utils import save_audio_to_file
from .vad_interface import VADInterface


class VoskVAD(VADInterface):
    """
    Реализация интерфейса VADInterface на основе Vosk.
    """

    def __init__(self, **kwargs):
        """
        Инициализация конвейера VAD на основе Vosk.

        Аргументы:
            model_path (str): Путь к директории с моделью Vosk.
        """
        self.model_path = kwargs.get("model_path", "values/vosk-model-small-ru-0.22")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Модель Vosk не найдена в {self.model_path}. Убедитесь, что модель загружена."
            )

        self.model = VoskModel(self.model_path)

    async def detect_activity(self, client):
        """
        Определяет голосовую активность в аудиоданных клиента.

        Аргументы:
            client (src.Client): Клиент, для которого проводится детекция.

        Возвращает:
            List: Список сегментов с голосовой активностью, содержащий "start", "end" и "confidence".
        """
        audio_file_path = None
        vad_segments = []

        try:
            # Сохранение аудиофайла из клиентского буфера
            audio_file_path = await save_audio_to_file(
                client.scratch_buffer, client.get_file_name()
            )

            with wave.open(audio_file_path, "rb") as wf:
                # Проверка формата WAV-файла
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                    raise ValueError(
                        "Аудиофайл должен быть в формате WAV, моно, 16-bit, 16 kHz"
                    )

                recognizer = KaldiRecognizer(self.model, wf.getframerate())
                recognizer.SetWords(True)
                recognizer.SetPartialWords(True)

                # Чтение фреймов и обработка результатов
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        if "result" in result:
                            vad_segments.extend(
                                {
                                    "start": word["start"],
                                    "end": word["end"],
                                    "confidence": word.get("conf", 1.0),
                                }
                                for word in result["result"]
                            )

                # Финальный результат (если есть)
                final_result = json.loads(recognizer.FinalResult())
                if "result" in final_result:
                    vad_segments.extend(
                        {
                            "start": word["start"],
                            "end": word["end"],
                            "confidence": word.get("conf", 1.0),
                        }
                        for word in final_result["result"]
                    )

        except wave.Error as e:
            raise RuntimeError(f"Ошибка обработки WAV-файла: {e}")

        except Exception as e:
            raise RuntimeError(f"Неожиданная ошибка: {e}")

        finally:
            # Удаляем временный файл, если он был создан
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)

        return vad_segments
