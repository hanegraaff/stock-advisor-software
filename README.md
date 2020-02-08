# Overview
A program that makes stock reccomendations depending on how closely analyst target prices agree with each other. It is based on the findings of this paper:

https://www8.gsb.columbia.edu/faculty-research/sites/faculty-research/files/FRANK%20ZHANG%20PAPER%20PSZ_20190913.pdf

It suggests, among other things, that when taken individually or even on average, analyst price targets are not a good predictor of returns, but when there is low variance between them then there is a positive correlation with returns, especially when the target price is high compared to the current one.

The code presented here is based one the ```security-valuator``` project

https://github.com/hanegraaff/security-valuator

## Paper Abstract
Consensus analyst target prices are widely available online at no cost to investors. In this paper we consider whether these consensus target prices are informative for predicting future returns. We find that when considered in isolation, consensus target prices are not generally informative about future returns. However, we also show that the dispersion of individual analysts’ target prices that comprise the consensus is an important moderating factor. More specifically, when dispersion is low (high), there is a strong positive (negative) correlation between predicted returns based on the consensus target price and future realized returns. Additional analyses suggest that this phenomenon is due to consensus target prices being slow to reflect bad news. Finally, we show that the negative correlation between consensus-based predicted returns and future realized returns for high-dispersion stocks exists only for high short interest and low institutional ownership, suggesting that limits to arbitrage play a role in the observed mispricing and that unsophisticated investors are negatively impacted by high consensus target prices.

## Release Notes (v0.1)
This is the first version with very limited functionality.

* Display analyst metrics to console
* Store results to cache

Zacks data is similar to, but does not exactly match other sources like Yahoo Finance.

## Prerequisites
### API Keys
An API Key for the Intrinio (https://www.intrinio.com) with access to the "US Fundamentals and Stock Prices" and "Zacks Price Targets" feeds

the API must be saved to the environment like so:

```export INTRINIO_API_KEY=[your API key]```

### Installing requirements
```pip install -r requirements.txt```

You may run this in a virtual environment like so:

```
python3 -m venv venv
source venv/bin/activate

cd src
pip install -r requirements.txt
```

## Running the script
All scripts must be executed from the ```src``` folder.

```
src >>python analyze_securities.py -h
usage: analyze_securities.py [-h] [-ticker TICKER] [-ticker-file TICKER_FILE]

Analyzes securities and displays the degree price target consensus based on
Zacks market data provided by Intrinio. The input parameters can either be a
ticker symbol or a file containing a list of them. The output is a dictionary
printed to the console containing price target metrics.

optional arguments:
  -h, --help            show this help message and exit
  -ticker TICKER        Ticker Symbol
  -ticker-file TICKER_FILE
                        Ticker Symbol file
```

Examples:

```
python analyze_securities.py -ticker-file ticker-list.txt
python analyze_securities.py -ticker AAPL
```

## Output
```
src >>python analyze_securities.py -ticker AAPL
[INFO] - {
    "ticker": "AAPL",
    "target_price_count": 26.0,
    "target_price_sdtdev": 53.974,
    "target_price_avg": 305.076,
    "target_price_sdtdev_pct": "17.692",
    "current_price": 318.31
}
```

Here we we can see that 

```"target_price_count": 26.0```
and
```"target_price_sdtdev_pct": "17.843"```

mean that out 26 analyst targets most of them (the standard deviation) are within 17.843% of the mean, so there is a level of disagreement that is not trivial. The other values represent the other price metrics are are available to see.

We can also see that the current price is ```318.31``` USD and the average price target is ```305.076```

## Caching of financial data
All financial data is saved to a local cache to reduce reliance on the Intrinio API. As of this version the data is set to never expire, and the cache will grow to a maximum size of 4GB.

The cache is located in the following path:

```
./financial-data/
./financial-data/cache.db
```

To delete or reset the contents of the cache, simply delete entire ```./financial-data/``` folder

## Unit testing
You may run all unit tests using this command:

```./test.sh```

This command will execute all unit tests and run the coverage report (using coverage.py)

```
src >>./test.sh

Ran 27 tests in 0.022s

OK
Name                             Stmts   Miss  Cover
----------------------------------------------------
data_provider/intrinio_data.py     103     41    60%
data_provider/intrinio_util.py      13      0   100%
exception/exceptions.py             27      1    96%
support/financial_cache.py          31      0   100%
support/util.py                     11      1    91%
----------------------------------------------------
TOTAL                              185     43    77%
```

## What's next?
1) Analyze large groups of securitues
2) Apply filters to display the best candidates
3) Apply additional filters. For example we could look at financial statements and other metrics to judge the quality of an investment.