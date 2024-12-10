import os
import sys
import time

# import json
import shutil

# import signal
import logging

# import requests
import argparse

# import threading
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

import leafbr.datasets.utils as utils
import leafbr.datasets.config as config

logger = logging.getLogger(__name__)
# stop_event = threading.Event()


def split_to_scraping(
    output_dir: Path = config.OUTPUT_DIR,
    tipo_bula: config.TipoBula = config.TipoBula.PACIENTE,
    num_threads: int = config.NUM_THREADS,
) -> int:
    logger.info("Started split_to_scraping")
    output_dir = output_dir / tipo_bula.name.lower()
    os.makedirs(output_dir, exist_ok=True)

    # valid_drugs = utils.get_valid_drugs()

    remain_drugs = utils.get_remained_drugs(tipo_bula=tipo_bula)

    logger.info(f"There are {len(remain_drugs)} drugs left to be downloaded")

    drugs_split = np.array_split(remain_drugs.index.to_list(), num_threads)
    total_scrapped = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for thread, drugs_part in enumerate(drugs_split):
            future = executor.submit(
                download_leaflets,
                thread,
                drugs_part,
                output_dir,
                tipo_bula,
            )
            futures.append(future)
            time.sleep(config.TIME_BETWEEN_THREADS)

        for future in concurrent.futures.as_completed(futures):
            total_scrapped += future.result()

    remain_drugs = utils.get_remained_drugs(tipo_bula=tipo_bula)
    logger.info(
        f"There are {len(remain_drugs)} drugs left to be downloaded, execute script again if it need"
    )

    return len(remain_drugs)


def download_leaflets(
    thread: int,
    drugs: list,
    output_dir: Path,
    tipo_bula,
) -> int:
    logger.info(f"Starting Selenium in Thread {thread}")

    tmp_dir = output_dir / f"tmp{thread}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)

    tmp_dir.mkdir(exist_ok=True)

    driver = get_driver(tmp_dir)

    scraped = 0

    logger.info("Got Driver, starting scraping")

    for drug in drugs:
        # if stop_event.is_set():
        #     logger.info(f"Stopping scraping in thread {thread} due to signal")
        #     break

        logger.info(f"Drug {drug}")

        try:
            find_and_download(driver, config.URL % drug, tipo_bula)
        except Exception as e:
            logger.error(f"Error finding {drug}")

        try:
            move_file(tmp_dir, output_dir / f"{drug}.pdf")
            scraped += 1
            logger.info(f"Success {drug}")
        except:
            logger.error(f"Error {drug}")

    driver.quit()
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return scraped


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

    except Exception as e:
        logger.error(f"Error finding the element")
        raise


@retry(tries=10, delay=1, backoff=1.5, logger=logger)
def move_file(tmp_dir: Path, output_file: Path):
    files = os.listdir(tmp_dir)
    if len(files) == 0:
        logging.info("Nothing here")

    elif len(files) == 1:
        shutil.move(tmp_dir / files[0], output_file)
        print("Renamed %s to %s" % (tmp_dir / files[0], output_file))
        logging.info("Renamed %s to %s" % (tmp_dir / files[0], output_file))

    else:
        logging.error(
            "Some files not be move. Deleting all tmp files because there no way to say who are them"
        )
        for file in tmp_dir.iterdir():
            if file.is_file():
                file.unlink()


def get_driver(download_dir: Path):
    logging.info(f"Data will be downloaded in {download_dir.absolute().as_posix()}")
    chrome_options = Options()

    prefs = {
        "download.default_directory": download_dir.absolute().as_posix(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)

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


def main():
    args = parse_arguments()

    attemps = []
    while (
        remain := split_to_scraping(
            args.output_dir,
            args.tipo_bula,
            args.num_threads,
        )
        != 0
    ):
        attemps.append(remain)
        if args.max_attempts != -1 and len(attemps) >= args.max_attempts:
            sys.exit(1)

    # clean_up(args.output_dir, args.num_threads)
    sys.exit(0)


# Função de limpeza para ser chamada ao encerrar
def clean_up(output_dir: Path, num_threads: int):
    for thread in range(num_threads):
        tmp_dir = output_dir / f"tmp{thread}"
        if tmp_dir.exists():
            logger.info(f"Removing temporary directory: {tmp_dir}")
            shutil.rmtree(tmp_dir)


# # Handler para capturar o Ctrl + C e acionar o stop_event
# def signal_handler(sig, frame):
#     logger.info("Signal received, cleaning up and stopping threads...")
#     stop_event.set()
#     clean_up(config.OUTPUT_DIR, config.NUM_THREADS)
#     sys.exit(0)


def tipo_bula_converter(value):
    try:
        return config.TipoBula[value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"{value} is not a valid TipoBula. Choose from {', '.join(e.name.lower() for e in config.TipoBula)}"
        )


def parse_arguments():
    parser = argparse.ArgumentParser(description="Script de scraping")

    parser.add_argument(
        "--num-threads",
        type=int,
        default=config.NUM_THREADS,
        help="Número de threads para scraping",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.OUTPUT_DIR,
        help="Diretório de saída para os arquivos baixados",
    )
    parser.add_argument(
        "--tipo-bula",
        type=tipo_bula_converter,
        default=config.TipoBula.PACIENTE,
        help="Tipo de bula a ser baixada",
    )
    parser.add_argument(
        "--max-attempts", type=int, default=-1, help="Número máximo de tentativas para o scraping"
    )

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            # logging.StreamHandler(sys.stdout),
        ],
        format="%(asctime)s %(levelname)s [Thread %(thread)d]: %(message)s",
        level=logging.INFO,
    )

    main()
    utils.normalize_and_update()
