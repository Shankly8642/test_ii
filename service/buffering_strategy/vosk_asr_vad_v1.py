import asyncio
import json
import os
import time



from .buffering_strategy_interface import BufferingStrategyInterface
from service.nlp.event_parser import parse_event
from service.nlp.qa_system import get_answer_to_question
from spacy.matcher import Matcher
import spacy

from words2numsrus import NumberExtractor

nlp = spacy.load("ru_core_news_sm")
extractor = NumberExtractor()

class VoskAsrVadv1(BufferingStrategyInterface):
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

        self.chunk_length_seconds = float(
            kwargs.get("chunk_length_seconds", 5.0))
        self.chunk_offset_seconds = float(
            kwargs.get("chunk_offset_seconds", 0.1))
        self.activation_keywords = kwargs.get(
            "activation_keywords", ["мульти","мультик", "мультиварка", "мультиварочка", "сварка", "ручка", "чка"]
        )
        self.processing_flag = False


    def process_audio(self, websocket, vad_pipeline, asr_pipeline):
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
                self.process_audio_async(websocket, vad_pipeline, asr_pipeline)
            )


    async def process_audio_async(self, websocket, vad_pipeline, asr_pipeline):
        try:
            transcription = await asr_pipeline.transcribe(self.client)
            text = transcription.get("text", "").strip()
            if not text:
                self.processing_flag = False
                return

            # Проверяем на обращение к системе
            extracted_command = self.extract_after_call(text)
            if not extracted_command:
                await websocket.send(
                    json.dumps({"error": "No system call detected."}))
                self.processing_flag = False
                return

            # Преобразуем текстовые числа в цифровой формат
            extracted_command = self.words_num_replace_num(extracted_command)

            # Проверяем на событие
            event_name, event_data = parse_event(extracted_command)
            if event_name:
                response = {
                    "event": event_name,
                    "data": event_data,
                }
                await websocket.send(json.dumps(response))
            else:
                # Если событие не найдено, используем Q&A
                recipe_text = ("""
Возьмите 2 стакана муки, 1 стакан сахара, 1 стакан молока, 2 яйца и 1 чайную ложку разрыхлителя.
Смешайте муку, сахар и разрыхлитель в большой миске.
Добавьте молоко и яйца, хорошо перемешайте.
Вылейте тесто в форму для выпекания.
Выпекайте при температуре 180 градусов Цельсия в течение 30 минут.
""")  # Добавьте ваш текст рецепта
                recipe_text = self.words_num_replace_num(recipe_text)
                answer = get_answer_to_question(recipe_text, extracted_command)
                print(answer)
                if (answer.encode() != recipe_text.encode()):
                    await websocket.send(json.dumps({"answer": answer}))

            json.dumps({"error": "Не вопрос и не событие"})

        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))
        finally:
            self.client.scratch_buffer.clear()
            self.processing_flag = False


    def extract_after_call(self, text):
        """
        Проверяет, содержит ли текст обращение к системе.
        """
        print(text)
        matcher = Matcher(nlp.vocab)
        for keyword in self.activation_keywords:
            pattern = [{"LOWER": {"REGEX": f"^{keyword}"}}]
            matcher.add("CALL_PATTERN", [pattern])

        doc = nlp(text.lower())
        matches = matcher(doc)
        if matches:
            _, start, end = matches[0]
            return doc[end:].text.strip()
        return None


    def words_num_replace_num(self, text):
        """
        Преобразует текстовые числа в цифровой формат.
        """
        return extractor.replace_groups(text)


""" async def process_audio_async(self, websocket, vad_pipeline, asr_pipeline):

        Асинхронно обрабатывает аудио для детекции активности и транскрипции.

        Этот метод выполняет ресурсоемкую обработку, включая детекцию голосовой
        активности и транскрипцию аудиоданных. Он отправляет результаты
        транскрипции через веб-сокет.

        Аргументы:
            websocket (Websocket): Веб-сокет для отправки результатов
                                   транскрипции.
            vad_pipeline: Конвейер для детекции голосовой активности.
            asr_pipeline: Конвейер для автоматического распознавания речи.

        try:
            transcription = await asr_pipeline.transcribe(self.client)
            text = transcription.get("text", "").strip()
            if not text:
                self.processing_flag = False
                return

            # Проверяем на обращение к системе
            extracted_command = self.extract_after_call(text)
            if not extracted_command:
                await websocket.send(
                    json.dumps({"error": "No system call detected."}))
                self.processing_flag = False
                return

            # Преобразуем текстовые числа в цифровой формат
            extracted_command = self.words_num_replace_num(
                extracted_command)


        start = time.time()
        vad_results = await vad_pipeline.detect_activity(self.client)

        if len(vad_results) == 0:
            self.client.scratch_buffer.clear()
            self.client.buffer.clear()
            self.processing_flag = False
            return

        last_segment_should_end_before = (
            len(self.client.scratch_buffer)
            / (self.client.sampling_rate * self.client.samples_width)
        ) - self.chunk_offset_seconds
        if vad_results[-1]["end"] < last_segment_should_end_before:
            transcription = await asr_pipeline.transcribe(self.client)
            if transcription["text"] != "":
                end = time.time()
                transcription["processing_time"] = end - start
                json_transcription = json.dumps(transcription)
                await websocket.send(json_transcription)
            self.client.scratch_buffer.clear()
            self.client.increment_file_counter()

        self.processing_flag = False """


