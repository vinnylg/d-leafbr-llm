import os
import pandas as pd
from pathlib import Path


# get all drugs with valid register number
def get_all_drugs(filename):
    df = pd.read_csv(filename, sep=";", encoding="cp1252")
    df.columns = df.columns.str.lower()

    df = df.loc[df["numero_registro_produto"].notna()].copy()
    df["numero_registro_produto"] = df["numero_registro_produto"].astype(int)
    df.set_index("numero_registro_produto", inplace=True)

    df = df.map(lambda x: x.lower() if type(x) is str else None)

    return df


output_list = lambda output_dir: os.listdir(output_dir)


def get_valid_drugs(filename):
    df = pd.read_csv(filename, sep=";", encoding="cp1252")
    df.columns = df.columns.str.lower()

    df = df.loc[df["numero_registro_produto"].notna()].copy()
    df["numero_registro_produto"] = df["numero_registro_produto"].astype(int)
    df.set_index("numero_registro_produto", inplace=True)

    df = df.map(lambda x: x.lower() if type(x) is str else None)

    return df.loc[df["situacao_registro"] == "válido"]


output_list = lambda output_dir: os.listdir(output_dir)


def get_remained_drugs(df, output_dir):
    files = output_list(output_dir)
    drugs = [int(x) if x.isnumeric() else 0 for x in map(lambda y: Path(y).stem, files)]

    return df.loc[~df.index.isin(drugs)]


def get_unchecked_drugs(checked_pdf, pdf_list):
    checked_set = set(checked_pdf.index.astype(str) + ".pdf")
    unchecked_pdf_list = [pdf for pdf in pdf_list if pdf not in checked_set]
    return unchecked_pdf_list


# def get_new_invalid_drugs(df, output_dir):
#     files = output_list(output_dir)
#     drugs = [ int(x) if x.isnumeric() else 0 for x in map(lambda y: Path(y).stem ,files) ]

#     get_all_drugs

#     return
