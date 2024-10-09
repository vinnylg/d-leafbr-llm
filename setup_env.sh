#!/bin/bash

# Instala o virtualenv e o virtualenvwrapper
python3 -m pip install virtualenv virtualenvwrapper

# Adiciona configurações necessárias ao .bashrc se ainda não estiverem lá
if ! grep -q "export WORKON_HOME=\$HOME/.virtualenvs" ~/.bashrc; then
    echo "export WORKON_HOME=\$HOME/.virtualenvs" >> ~/.bashrc
    echo "export WORKON_HOME=\$HOME/.virtualenvs"
fi

if ! grep -q "export VIRTUALENVWRAPPER_PYTHON=\$(which python3)" ~/.bashrc; then
    echo "export VIRTUALENVWRAPPER_PYTHON=\$(which python3)" >> ~/.bashrc
    echo "export VIRTUALENVWRAPPER_PYTHON=\$(which python3)"
fi

if ! grep -q "source /home/$USER/.local/bin/virtualenvwrapper.sh" ~/.bashrc; then
    echo "source /home/$USER/.local/bin/virtualenvwrapper.sh" >> ~/.bashrc
    echo "source /home/$USER/.local/bin/virtualenvwrapper.sh"
fi

# Carrega as novas configurações
source ~/.bashrc  # ou ~/.zshrc, se necessário
