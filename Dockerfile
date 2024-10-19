# Use a imagem base da NVIDIA para PyTorch com CUDA 12
FROM nvcr.io/nvidia/pytorch:24.09-py3
# pytorch/pytorch
RUN groupadd -r developer && useradd -r -g developer developer

# Configurações gerais
# ENV DEBIAN_FRONTEND=noninteractive
# ENV CHROME_BIN=/usr/bin/chromium-browser
# ENV CHROME_DRIVER=/usr/bin/chromedriver

# Instale as dependências de sistema necessárias
RUN apt-get update && apt-get install -y \
    git \
    vim \
    curl \
    wget \
    # gnupg \
    # apt-transport-https \
    # ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# RUN wget -N https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb -P ~/ \
#     && dpkg -i ~/google-chrome-stable_114.0.5735.90-1_amd64.deb || apt-get install -fy


# RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` \
#     && wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P ~/ \
#     && unzip ~/chromedriver_linux64.zip -d ~/ \
#     && rm ~/chromedriver_linux64.zip \
#     && mv -f ~/chromedriver /usr/local/bin/chromedriver \
#     && chown root:root /usr/local/bin/chromedriver \
#     && chmod 0755 /usr/local/bin/chromedriver

COPY . /workspace
WORKDIR /workspace

# Atualize pip e instale dependências do Python
RUN pip install --upgrade pip

# Instale outras bibliotecas adicionais que você precisa (se houver)
RUN pip install --no-cache-dir -r requirements.txt

# RUN chown -R developer:developer /workspace
# USER developer

# Cria um usuário com UID e GID específicos
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

# Cria o grupo e o usuário
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Usa o novo usuário por padrão
USER $USERNAME