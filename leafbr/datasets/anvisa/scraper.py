import os
import sys
import time
import json
import shutil
import logging
import requests
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from retry import retry
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import leafbr.datasets.anvisa.utils as utils
import leafbr.datasets.anvisa.config as config

logger = logging.getLogger(__name__)


def get_driver(output_dir: Path, remote: bool = config.SELENIUM_REMOTE):
    logging.info(f"Data will be downloaded in {output_dir.absolute().as_posix()}")
    chrome_options = Options()

    prefs = {
        "download.default_directory": output_dir.absolute().as_posix(),  # Diretório para download
        "download.prompt_for_download": False,  # Não solicitar download
        "download.directory_upgrade": True,  # Permitir substituição do diretório
        "safebrowsing.enabled": True,  # Habilitar navegação segura
    }

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    if remote:
        logging.info(f"Tryna Starting Seleniun Remote")

        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        driver = webdriver.Remote(
            command_executor="http://selenium-hub:4444/wd/hub",
            options=chrome_options,
        )

        # driver = webdriver.Chrome(options=chrome_options)

    else:
        logging.info(f"Tryna Starting Seleniun ib Host")

        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        chrome_options.add_argument("--start-maximized")

        driver = webdriver.Chrome(
            options=chrome_options, service=ChromeService(ChromeDriverManager().install())
        )

    logging.info(f"Driver Connected")
    return driver


def split_to_scraping(
    output_dir=config.OUTPUT_DIR,
    tipo_bula: config.TipoBula = config.TipoBula.PACIENTE,
) -> int:
    logger.info("Started split_to_scraping")
    output_dir = output_dir / tipo_bula.name.lower()
    os.makedirs(output_dir, exist_ok=True)

    all_drugs = utils.get_valid_drugs(config.DADOS_ABERTOS)
    logger.info(f"There are {len(all_drugs)} valid drugs in {config.DADOS_ABERTOS}")

    remain_drugs = utils.get_remained_drugs(all_drugs, output_dir)
    # count_while = 0

    # while not remain_drugs.empty:
    #     count_while += 1
    #     logger.info(f"Attempt {count_while} to download remaining drugs")
    logger.info(f"There are {len(remain_drugs)} drugs left to be downloaded")

    drugs_split = np.array_split(remain_drugs.index.to_list(), config.NUM_THREADS)
    total_scrapped = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.NUM_THREADS) as executor:
        futures = []
        for i, drugs_part in enumerate(drugs_split):
            future = executor.submit(download_leaflets, drugs_part, output_dir, tipo_bula, i)
            futures.append(future)
            time.sleep(config.TIME_BETWEEN_THREADS)

        for future in concurrent.futures.as_completed(futures):
            total_scrapped += future.result()

    # logger.info(f"Finished attempt {count_while}, {total_scrapped} drugs downloaded")
    remain_drugs = utils.get_remained_drugs(all_drugs, output_dir)
    logger.info(
        f"There are {len(remain_drugs)} drugs left to be downloaded, execute script again if it need"
    )

    return len(remain_drugs)


def download_leaflets(
    drugs: list,
    output_dir: Path,
    tipo_bula: config.TipoBula,
    i: int = -1,
) -> int:
    logger.info(f"Starting Selenium in Thread {i}")

    tmp_dir = output_dir / f"tmp{i}"
    tmp_dir.mkdir(exist_ok=True)

    driver = get_driver(tmp_dir)

    scraped = 0

    logger.info("Got Driver, starting scraping")

    for drug in drugs:
        logger.info(f"Drug {drug}")

        try:
            find_and_download(driver, config.URL % drug, tipo_bula)
            move_file(tmp_dir, output_dir / f"{drug}.pdf")
            scraped += 1
            logger.info(f"Sucess {drug}")

        except Exception as e:
            logger.error(f"Error downloading {drug}: {e}")

    driver.quit()  # Certifique-se de fechar o driver após a execução
    shutil.rmtree(tmp_dir)
    return scraped


@retry(tries=10, delay=1, backoff=1.5, logger=logger)
def move_file(tmp_dir: Path, output_file: Path):
    logging.info("Rename %s" % tmp_dir)
    files = os.listdir(tmp_dir)
    shutil.move(tmp_dir / files[0], output_file)


@retry(tries=config.TRIES, delay=config.DELAY, backoff=config.BACKOFF, logger=logger)
def find_and_download(driver, url, element: config.TipoBula):
    logger.info("Try download")
    try:
        logger.info(f"Getting {url}")
        driver.get(url)
        download_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(@ng-if, '{element.value}')]"))
        )

        logger.info(f"click in download")

        download_button.click()
        # filename = get_filename(driver)

        # if not filename:
        #     raise Exception("Element found but not downloaded")

        # return filename
    except Exception as e:
        logger.error(f"Error finding the element: {e}")
        raise


# def get_filename(driver) -> str:
#     logger.info("Check metadata")
#     logs = driver.get_log("performance")
#     for entry in logs:
#         obj = json.loads(entry["message"])
#         if (
#             "response" in obj["message"]["params"].keys()
#             and "https://consultas.anvisa.gov.br/api/consulta/medicamentos/arquivo/bula/"
#             in obj["message"]["params"]["response"]["url"]
#             and obj["message"]["params"]["response"]["status"] == 200
#         ):
#             filename = (
#                 obj["message"]["params"]["response"]["headers"]["content-disposition"]
#                 .split("filename=")[1]
#                 .strip('"')
#             )
#             if filename:
#                 return filename

#     return None


def main():

    parser = argparse.ArgumentParser(description="Script de scraping")
    parser.add_argument("--max-attemps", type=int, default=-1, help="Número máximo de tentativas")
    args = parser.parse_args()

    max_attemps = args.max_attemps

    attemps = []
    while remain := split_to_scraping() != 0:
        attemps.append(remain)

        if max_attemps != -1 and len(attemps) >= max_attemps:
            sys.exit(1)
        elif len(attemps) >= 3 and attemps[-3] == attemps[-2] == attemps[-1]:
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
        format="%(asctime)s %(levelname)s [Thread %(thread)d]: %(message)s",
        level=logging.INFO,
    )

    main()
