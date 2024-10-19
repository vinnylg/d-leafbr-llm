from enum import Enum
from leafbr.config import EXTERNAL_DATA_DIR, RAW_DATA_DIR, LOG_DIR

SELENIUM_REMOTE = True
NUM_THREADS = 24
TIME_BETWEEN_THREADS = 1
TRIES = 1  # 10
DELAY = 1  # 1
BACKOFF = 1.5  # 1.5


DADOS_ABERTOS = EXTERNAL_DATA_DIR / "DADOS_ABERTOS_MEDICAMENTOS.csv"
OUTPUT_DIR = RAW_DATA_DIR / "anvisa"
LOG_FILE = LOG_DIR / "leafbr.datasets.anvisa.scraper.log"

URL = "https://consultas.anvisa.gov.br/#/bulario/q/?numeroRegistro=%s"


class TipoBula(Enum):
    PROFISSIONAL = "produto.idBulaProfissionalProtegido"
    PACIENTE = "produto.idBulaPacienteProtegido"
