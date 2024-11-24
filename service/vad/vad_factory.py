from .vosk_vad import VoskVAD


class VADFactory:
    """
    Фабрика для создания экземпляров систем VAD (детекция голосовой активности).
    """

    @staticmethod
    def create_vad_pipeline(type, **kwargs):
        """
        Создает конвейер VAD на основе указанного типа.

        Аргументы:
            type (str): Тип конвейера VAD для создания (например, 'pyannote').
            kwargs: Дополнительные аргументы для создания конвейера VAD.

        Возвращает:
            VADInterface: Экземпляр класса, реализующего интерфейс VADInterface.

        Исключения:
            ValueError: Если указанный тип конвейера VAD не поддерживается.
        """

        return VoskVAD(**kwargs)
        if type == "pyannote":
            return PyannoteVAD(**kwargs)
        else:
            raise ValueError(f"Неизвестный тип конвейера VAD: {type}")
