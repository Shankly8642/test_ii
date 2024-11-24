class BufferingStrategyInterface:
    """
    Интерфейс для стратегий буферизации в системах обработки аудио.

    Этот класс определяет структуру для стратегий буферизации, используемых
    при обработке аудиоданных. Он служит шаблоном для создания пользовательских
    стратегий буферизации, которые соответствуют специфическим требованиям
    конвейера обработки аудио.

    Подклассы должны реализовывать методы, определенные в этом интерфейсе, чтобы
    обеспечить согласованность и совместимость с системой обработки аудио.

    Методы:
        process_audio: Обработка аудиоданных. Этот метод должен быть
                       реализован в подклассах.
    """

    def process_audio(self, websocket, vad_pipeline, asr_pipeline):
        """
        Обрабатывает аудиоданные с использованием заданного веб-сокета,
        конвейера VAD и конвейера ASR.

        Этот метод предназначен для переопределения в подклассах с целью
        предоставления конкретной логики обработки аудиоданных в рамках разных
        стратегий буферизации.

        Аргументы:
            websocket (Websocket): Веб-сокет для связи с клиентами.
            vad_pipeline: Конвейер детекции голосовой активности (VAD),
                          используемый для определения речи в аудио.
            asr_pipeline: Конвейер автоматического распознавания речи (ASR),
                          используемый для транскрипции речи из аудио.

        Исключения:
            NotImplementedError: Если метод не реализован в подклассе.
        """
        raise NotImplementedError(
            "Этот метод должен быть реализован в подклассах."
        )
