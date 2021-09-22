import Scrape
import config 

tickers = config.TICKERS

for tic in tickers:
    try:
        Scrape.price_updater(tic)