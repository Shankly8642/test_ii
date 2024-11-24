from .realtime_vosk_transcribe import RealtimeVoskTranscribe
from .vosk_asr_vad_v1 import VoskAsrVadv1;
from .vosk_asr_vad import VoskAsrVad;


class BufferingStrategyFactory:
    """
    Фабричный класс для создания экземпляров различных стратегий буферизации.

    Этот фабричный класс предоставляет централизованный способ создания
    различных стратегий буферизации на основе указанного типа. Он абстрагирует
    логику создания, упрощая управление и добавление новых типов стратегий
    буферизации.

    Методы:
        create_buffering_strategy: Создает и возвращает экземпляр
                                   указанной стратегии буферизации.
    """

    @staticmethod
    def create_buffering_strategy(type, client, **kwargs):
        """
        Создает экземпляр стратегии буферизации на основе
        указанного типа.

        Этот метод работает как фабрика для создания объектов стратегий
        буферизации. Он возвращает экземпляр стратегии, соответствующей
        указанному типу. Если тип не распознан, генерируется ValueError.

        Аргументы:
            type (str): Тип стратегии буферизации для создания. В данный момент
                        поддерживается 'realtime_vosk_transcribe'.
            client (Client): Экземпляр клиента, связанный со стратегией
                             буферизации.
            **kwargs: Дополнительные именованные аргументы, специфичные для
                      создаваемой стратегии буферизации.

        Возвращает:
            Экземпляр указанной стратегии буферизации.

        Исключения:
            ValueError: Если указанный тип не распознан или не поддерживается.

        Пример:
            strategy = BufferingStrategyFactory.create_buffering_strategy(
                       "realtime_vosk_transcribe", client
                       )
        """
        return VoskAsrVadv1(client, **kwargs)
        return VoskAsrVad(client, **kwargs)

        if type == "realtime_vosk_transcribe":
            return RealtimeVoskTranscribe(client, **kwargs)
        else:
            raise ValueError(f"Неизвестный тип стратегии буферизации: {type}")
