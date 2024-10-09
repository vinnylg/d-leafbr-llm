# Use a imagem base da NVIDIA para PyTorch com CUDA 12
FROM nvcr.io/nvidia/pytorch:23.07-py3

# Configurações gerais
ENV DEBIAN_FRONTEND=noninteractive

# Instale as dependências de sistema necessárias
RUN apt-get update && apt-get install -y \
    git \
    vim \
    curl \
    wget \
    make \
    && rm -rf /var/lib/apt/lists/*

# Atualize pip e instale dependências do Python
RUN pip install --upgrade pip

# Instale outras bibliotecas adicionais que você precisa (se houver)
RUN pip install -r requirements.txt

# Configurar Hugging Face CLI (opcional para login e autenticação)
# Você pode realizar login com token para acesso a modelos privados
RUN huggingface-cli login

# Defina o diretório de trabalho
WORKDIR /workspace

# Copia os arquivos de código para o container (útil se precisar de algo fixo no build)
# ADD ./seu_codigo /workspace

# Comando padrão ao iniciar o container
CMD ["bash"]
