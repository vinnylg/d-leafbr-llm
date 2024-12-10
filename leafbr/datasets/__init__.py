from pathlib import Path
import requests
import shutil

from leafbr.datasets.config import DADOS_ABERTOS

if not DADOS_ABERTOS.exists():
    with requests.get(
        "https://dados.anvisa.gov.br/dados/DADOS_ABERTOS_MEDICAMENTOS.csv", stream=True
    ) as r:
        with open(DADOS_ABERTOS, "wb") as f:
            shutil.copyfileobj(r.raw, f)
