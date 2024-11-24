import os
import wave
import json
import subprocess
import shutil
from vosk import Model, KaldiRecognizer
from utils.audio_utils import save_audio_to_file
from .asr_interface import ASRInterface


def download_and_extract_model(model_url, model_zip, model_dir):
    """
    Скачивает и извлекает модель Vosk, если она не установлена.

    :param model_vosk_url: URL для скачивания модели.
    :param model_vosk_zip: Имя zip-файла модели.
    :param model_vosk_dir: Директория для установки модели.
    """
    if not os.path.exists(model_dir):
        print("Скачивание модели...")
        subprocess.run(["wget", model_url, "-O", model_zip], check=True)
        subprocess.run(["unzip", model_zip], check=True)
        extracted_dir = model_zip.replace(".zip", "")
        shutil.move(extracted_dir, model_dir)
        os.remove(model_zip)
        print("Модель успешно скачана и установлена.")


class VoskASR(ASRInterface):
    def __init__(self, **kwargs):
        self.model_dir = kwargs.get("model_vosk_dir", "values/vosk-model-small-ru-0.22")
        self.model_url = kwargs.get(
            "model_vosk_url", "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
        )
        self.model_zip = kwargs.get("model_vosk_zip", "values/vosk-model-small-ru.zip")

        # Убедимся, что модель загружена и установлена
        download_and_extract_model(self.model_url, self.model_zip, self.model_dir)

        # Загружаем модель
        self.model = Model(self.model_dir)

    async def transcribe(self, client):
        """
        Расшифровывает аудиоданные клиента с использованием Vosk.

        :param client: Объект клиента с буфером аудиоданных.
        :return: Структура транскрипции.
        """
        # Сохраняем аудиоданные во временный файл
        file_path = await save_audio_to_file(
            client.scratch_buffer, client.get_file_name()
        )

        # Проверяем аудиофайл на соответствие требованиям Vosk
        wf = wave.open(file_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            wf.close()
            os.remove(file_path)
            raise ValueError("Аудиофайл должен быть в формате WAV, моно, 16-bit, 16 kHz")

        # Создаем распознаватель
        rec = KaldiRecognizer(self.model, 16000)
        text = ""

        # Расшифровка аудиофайла
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text += result.get("text", "") + " "

        # Закрываем файл и удаляем временный аудиофайл
        wf.close()
        os.remove(file_path)

        # Возвращаем результат в нужной структуре
        return {
            "language": "ru",
            "language_probability": None,
            "text": text.strip(),
            "words": "UNSUPPORTED_BY_VOSK",  # Для Vosk поддержка слов по умолчанию отсутствует
        }
