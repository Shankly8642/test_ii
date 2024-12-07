from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
import json
# Путь к локальной модели
model_directory = "./models/mdeberta-v3-base-squad2"

# Инициализация пайплайна с использованием локальной модели
qa_pipeline = pipeline(
    task='question-answering',
    model=AutoModelForQuestionAnswering.from_pretrained(model_directory),
    tokenizer=AutoTokenizer.from_pretrained(model_directory)
)

# Функция для получения ответа на вопрос по рецепту
def get_answer_to_question(context, question):
    result = qa_pipeline(question=question, context=context)
    raw_answer = result['answer']
    return raw_answer
