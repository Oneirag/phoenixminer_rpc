#!/usr/bin/env python
import time

import pandas as pd
import requests
from phoenixminer_rpc import is_debugging
from phoenixminer_rpc import logger, config, wallet, START_MINER_DELAY, MAX_TEMP
from phoenixminer_rpc.reboot import reboot
from phoenixminer_rpc.aemet import Aemet
from phoenixminer_rpc.power_prices_calendar import peak_price

coin = "eth"
coin = "etc"

nanopool_url = 'https://api.nanopool.org/v1/{coin}/hashrate/{WALLET}/{WORKER}'.format(
    WALLET=wallet, WORKER=config("WORKER"), coin=config("COIN", coin)
)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
}

logger.info("Starting nanopool speed check process")
time.sleep(START_MINER_DELAY if not is_debugging() else 0)  # Wait 15 min to start checking
aemet = Aemet()
while True:
    json = dict()
    logger.info("Checking connection to nanopool")
    try:
        req = requests.get(nanopool_url, headers=headers)
        json = req.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.RetryError,
            requests.exceptions.ConnectTimeout) as ce:
        logger.exception("Rebooting due to connection error to nanopool, internet connection down")
        reboot()
    except Exception as e:
        logger.exception(f"Rebooting due to exception while connecting to nanopool: {e}")
        reboot()  # No connection: reboot
    logger.info(f"Data read from nanopool: {json}")
    hashrate = json.get('data', 0)

    # it should have been peak at least 20 mins ago, as pool data refreshes
    # each 10 mins
    peak_time = pd.Timestamp.now() - pd.offsets.Minute(20)

    if hashrate == 0 and not peak_price(peak_time) and not peak_time():
        if aemet.get_pred_hour() > MAX_TEMP or aemet.get_pred_hour(h_offset=-1) > MAX_TEMP:
            logger.info("Current hashrate is 0, but forecast temp to high")
        else:
            logger.info("Current hashrate is 0, rebooting")
            reboot()

    time.sleep(1 * 60)  # Wait 1 min
