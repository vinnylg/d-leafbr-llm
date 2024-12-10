import os
import hashlib
import logging
import unicodedata
import pandas as pd
from pathlib import Path
from pandarallel import pandarallel

from leafbr.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR
from leafbr.datasets.config import DADOS_ABERTOS, TipoBula, OUTPUT_DIR

logger = logging.getLogger(__name__)


def get_all_drugs(filename: Path = DADOS_ABERTOS):
    df = pd.read_csv(filename, sep=";", encoding="cp1252")
    df.columns = df.columns.str.lower()

    df = df.loc[df["numero_registro_produto"].notna()].copy()
    df["numero_registro_produto"] = df["numero_registro_produto"].astype(int)
    df.set_index("numero_registro_produto", inplace=True)

    df = df.map(lambda x: x.lower() if type(x) is str else None)

    return df


def get_valid_drugs(filename: Path = DADOS_ABERTOS):
    df = pd.read_csv(filename, sep=";", encoding="cp1252")
    df.columns = df.columns.str.lower()

    df = df.loc[df["numero_registro_produto"].notna()].copy()
    df["numero_registro_produto"] = df["numero_registro_produto"].astype(int)
    df.set_index("numero_registro_produto", inplace=True)

    # df = df.map(lambda x: x.lower() if type(x) is str else None)
    df = df.map(lambda x: remove_accents(x).lower() if isinstance(x, str) else x)

    valid_drugs = df.loc[
        (df["situacao_registro"] == "valido") | (df["situacao_registro"] == "ativo")
    ].copy()

    logger.info(f"There are {len(valid_drugs)} valid drugs in {filename}")

    # Alguns medicamentos ou substâncias não possuem principio_ativo, mas o nome deles são ou podem ser, então vou considerar isso
    valid_drugs.loc[valid_drugs["principio_ativo"].isna(), "principio_ativo"] = valid_drugs.loc[
        valid_drugs["principio_ativo"].isna(), "nome_produto"
    ]

    valid_drugs["principio_ativo_composto"] = False
    valid_drugs.loc[
        valid_drugs["principio_ativo"].str.contains("+", regex=False), "principio_ativo_composto"
    ] = True

    valid_drugs["classe_terapeutica_composto"] = False
    valid_drugs.loc[
        valid_drugs["classe_terapeutica"].notna()
        & valid_drugs["classe_terapeutica"].str.contains("+", regex=False),
        "classe_terapeutica_composto",
    ] = True

    return valid_drugs


def get_download_leaflets(
    filename: Path = DADOS_ABERTOS,
    output_dir: Path = OUTPUT_DIR,
    tipo_bula: TipoBula = TipoBula.PACIENTE,
):
    output_dir = output_dir / tipo_bula.name.lower()
    valid_drugs = get_valid_drugs(filename)
    files = os.listdir(output_dir)
    drugs = [int(x) if x.isnumeric() else 0 for x in map(lambda y: Path(y).stem, files)]

    valid_drugs.loc[valid_drugs.index.isin(drugs), "filepath"] = output_dir / (
        valid_drugs.loc[valid_drugs.index.isin(drugs)].index.astype("str") + ".pdf"
    )

    pandarallel.initialize(nb_workers=12)
    valid_drugs.loc[valid_drugs["filepath"].notna(), "hash"] = valid_drugs.loc[
        valid_drugs["filepath"].notna(), "filepath"
    ].parallel_apply(hash)

    valid_drugs["bula_duplicada"] = valid_drugs.duplicated("hash", keep=False)

    return valid_drugs


def get_remained_drugs(
    output_dir: Path = OUTPUT_DIR,
    tipo_bula: TipoBula = TipoBula.PACIENTE,
):
    output_dir = output_dir / tipo_bula.name.lower()
    df = get_valid_drugs()
    files = os.listdir(output_dir)
    drugs = [int(x) if x.isnumeric() else 0 for x in map(lambda y: Path(y).stem, files)]

    return df.loc[~df.index.isin(drugs)]


def remove_accents(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    return text


def get_prebase():
    return pd.read_pickle(PROCESSED_DATA_DIR / "prebase.pkl")


def get_leafbr():
    pre_base = get_prebase()

    base = pre_base.loc[pre_base["bula_valida"] & ~pre_base["bula_duplicada"]]

    del base["tipo_produto"]
    del base["numero_processo"]
    del base["situacao_registro"]
    del base["bula_duplicada"]
    del base["bula_valida"]

    base.to_pickle(PROCESSED_DATA_DIR / "leafbr.pkl")
    base.to_json(PROCESSED_DATA_DIR / "leafbr.json", orient="index", default_handler=str)

    return base


def hash(filename):
    md5 = hashlib.md5()

    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    return md5.hexdigest()
