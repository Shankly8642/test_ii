class ASRInterface:
    async def transcribe(self, client):
        """
        Транскрибирует указанные аудиоданные.

        :param client: Объект клиента, содержащий все переменные-члены,
                       включая буфер с аудиоданными.
        :return: Структура транскрипции, например, см. файл
                 faster_whisper_asr.py.
        """
        raise NotImplementedError(
            "Этот метод должен быть реализован в подклассах."
        )
