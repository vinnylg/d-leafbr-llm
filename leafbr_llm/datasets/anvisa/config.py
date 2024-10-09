from enum import Enum
from leafbr_llm.config import EXTERNAL_DATA_DIR, RAW_DATA_DIR

NUM_THREADS = 12
TIME_BETWEEN_THREADS = 3
DADOS_ABERTOS= EXTERNAL_DATA_DIR / 'DADOS_ABERTOS_MEDICAMENTOS.csv'
OUTPUT_DIR = RAW_DATA_DIR / 'anvisa'

URL = "https://consultas.anvisa.gov.br/#/bulario/q/?numeroRegistro=%s"

class TipoBula(Enum):
    PROFISSIONAL = "produto.idBulaProfissionalProtegido"
    PACIENTE = "produto.idBulaPacienteProtegido"
