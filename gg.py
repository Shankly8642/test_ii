from transformers import AutoModelForQuestionAnswering, AutoTokenizer

model_name = "timpal0l/mdeberta-v3-base-squad2"
save_directory = "./models/mdeberta-v3-base-squad2"

# Скачивание модели и токенайзера
model = AutoModelForQuestionAnswering.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Сохранение модели и токенайзера в локальную директорию
model.save_pretrained(save_directory)
tokenizer.save_pretrained(save_directory)
