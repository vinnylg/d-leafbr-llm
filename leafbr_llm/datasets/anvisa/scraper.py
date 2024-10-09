import os
import sys
import time
import logging
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from retry import retry
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

import leafbr_llm.datasets.anvisa.utils as utils
import leafbr_llm.datasets.anvisa.config as config
from leafbr_llm.datasets.anvisa.downloader import download

logger = logging.getLogger(__name__)

# Renomeia partes de um caminho
rename_parts = lambda path, old, new: Path(*[new if x == old else x for x in path.parts])

def split_to_scraping(output_dir=config.OUTPUT_DIR, tipo_bula: config.TipoBula=config.TipoBula.PACIENTE):
    """
    Divide as drogas restantes em grupos e inicia o scraping dos PDFs.
    
    :param output_dir: Diretório onde os PDFs serão salvos.
    """
    logger.info('Started split_to_scraping')
    output_dir = output_dir / tipo_bula.name.lower()
    os.makedirs(output_dir, exist_ok=True)
    # os.makedirs(rename_parts(Path(output_dir), 'pdf', 'csv'), exist_ok=True)

    all_drugs = utils.get_valid_drugs()
    logger.info(f"There are {len(all_drugs)} drugs in csv file")

    remain_drugs = utils.get_remained_drugs(all_drugs, output_dir)
    count_while = 0

    while not remain_drugs.empty:
        count_while += 1
        logger.info(f"Attempt {count_while} to download remaining drugs")
        logger.info(f"There are {len(remain_drugs)} drugs left to be downloaded")

        drugs_split = np.array_split(remain_drugs.index.to_list(), config.NUM_THREADS)
        total_scrapped = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.NUM_THREADS) as executor:
            futures = []
            for drugs_part in drugs_split:
                future = executor.submit(scrapping_pdf, drugs_part, output_dir, tipo_bula)
                futures.append(future)
                time.sleep(config.TIME_BETWEEN_THREADS)

            for future in concurrent.futures.as_completed(futures):
                total_scrapped += future.result()

        logger.info(f'Finished attempt {count_while}, {total_scrapped} drugs downloaded')
        remain_drugs = utils.get_remained_drugs(all_drugs, output_dir)


def scrapping_pdf(drugs: list, output_dir: str, tipo_bula: config.TipoBula) -> int:
    """
    Realiza o scraping dos PDFs para uma lista de drogas.

    :param drugs: Lista de nomes de drogas.
    :param output_dir: Diretório onde os PDFs serão salvos.
    :return: Número de PDFs baixados com sucesso.
    """
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
    scraped = 0

    for drug in drugs:
        try:
            if (pdf_url := get_download_url(driver, config.URL % drug, tipo_bula)):
                if download(pdf_url, Path(output_dir) / Path(f"{drug}.pdf")):
                    logger.info('SUCCESS')
                    scraped += 1
        except Exception as e:
            logger.error(f"Error downloading {drug}: {e}")

    driver.quit()  # Certifique-se de fechar o driver após a execução
    return scraped


@retry(tries=5, delay=5, backoff=1.5, logger=logger)
def get_download_url(driver, url, element: config.TipoBula):
    """
    Obtém a URL do PDF a partir da página web.
    
    :param driver: Instância do webdriver.
    :param url: URL da página a ser acessada.
    :param element: Tipo de bula (profissional ou usuário).
    :return: URL do PDF encontrado.
    """
    try:
        logger.info(f"Getting {url}")
        driver.get(url)
        pdf_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(@ng-if, '{element.value}')]"))
        )
        return pdf_link.get_attribute('href')
    except Exception as e:
        logger.error(f"Error finding the element: {e}")
        raise
    

@retry(tries=5, delay=5, backoff=1.3, logger=logger)
def download(url: str, filename: str) -> bool:
    """
    Baixa um arquivo da URL especificada.
    
    :param url: URL do arquivo a ser baixado.
    :param filename: Caminho onde o arquivo será salvo.
    :return: True se o download for bem-sucedido, False caso contrário.
    """
    logger.info(f"Starting download: {filename}")
    r = requests.get(url, stream=True)

    r.raise_for_status()
    downloaded = 0

    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=1024):
            chunk_size = fd.write(chunk)
            downloaded += chunk_size

    logger.info(f'File size is: {downloaded}')

    if downloaded <= 1024:
        os.remove(filename)
        raise Exception(f"Download error: file size is too small {downloaded}")

    logger.info(f"{filename} downloaded successfully")
    return True
