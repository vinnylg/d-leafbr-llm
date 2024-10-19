import os
from huggingface_hub import login

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

if HF_TOKEN:
    login(token=HF_TOKEN)
    print("Login realizado com sucesso!")
else:
    print("HUGGINGFACE_TOKEN não encontrado. Verifique seu arquivo .env")