import pdfplumber
from pandarallel import pandarallel


from leafbr.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR
import leafbr.datasets.utils as u


def pdf2text(filename):
    print(f"extracting {filename}")
    text = ""
    try:
        with pdfplumber.open(filename) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        text = u.remove_accents(text.lower()) if isinstance(text, str) else ""

        return text.split("historico de alteracao da bula")[0].lower()
    except:
        print(f"error to extract {filename}")
        return ""


def extract(THREADS=12):
    pandarallel.initialize(nb_workers=THREADS)

    df = u.get_download_leaflets()
    df = df.loc[df["filepath"].notna()].copy()

    df["texto_bula"] = df["filepath"].parallel_apply(pdf2text)

    is_valid = [
        (nome in txt) or (pa in txt)
        for txt, nome, pa in zip(df["texto_bula"], df["nome_produto"], df["principio_ativo"])
    ]

    df["bula_valida"] = False
    df.loc[is_valid, "bula_valida"] = True

    df.to_pickle(PROCESSED_DATA_DIR / "prebase.pkl")
    df.to_json(PROCESSED_DATA_DIR / "prebase.json", orient="index", default_handler=str)


if __name__ == "__main__":
    extract(12)
