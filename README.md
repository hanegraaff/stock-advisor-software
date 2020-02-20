# Overview
A program that makes stock recommendations depending on how closely analyst target prices agree with each other. It is based on the findings of this paper:

https://www8.gsb.columbia.edu/faculty-research/sites/faculty-research/files/FRANK%20ZHANG%20PAPER%20PSZ_20190913.pdf

It suggests, among other things, that when taken individually or even on average, analyst price targets are not a good predictor of returns, but when there is low variance between them then there is a positive correlation with returns, especially when the target price is high compared to the current one.

The code presented here is based one the ```security-valuator``` project

https://github.com/hanegraaff/security-valuator

## Paper Abstract
Consensus analyst target prices are widely available online at no cost to investors. In this paper we consider whether these consensus target prices are informative for predicting future returns. We find that when considered in isolation, consensus target prices are not generally informative about future returns. However, we also show that the dispersion of individual analysts’ target prices that comprise the consensus is an important moderating factor. More specifically, when dispersion is low (high), there is a strong positive (negative) correlation between predicted returns based on the consensus target price and future realized returns. Additional analyses suggest that this phenomenon is due to consensus target prices being slow to reflect bad news. Finally, we show that the negative correlation between consensus-based predicted returns and future realized returns for high-dispersion stocks exists only for high short interest and low institutional ownership, suggesting that limits to arbitrage play a role in the observed mispricing and that unsophisticated investors are negatively impacted by high consensus target prices.

## Release Notes (v0.3)
This is an early version with limited functionality.

* Create and display portfolio recommendation based on a supplied ticker list
* Dispaly intermediate results

## Prerequisites
### API Keys
An API Key for the Intrinio (https://www.intrinio.com) with access to the "US Fundamentals and Stock Prices" and "Zacks Price Targets" feeds

the API must be saved to the environment like so:

```export INTRINIO_API_KEY=[your API key]```

### Installation requirements
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

usage: analyze_securities.py [-h] [-ticker-file TICKER_FILE] [-month MONTH]
                             [-year YEAR] [-portfolio_size PORTFOLIO_SIZE]

Generate a portfolio reccomendation based given a list a ticker symbols.
Selection is based on on the degree of analyst target price agreement,
specifically it will select stocks with the lower target price dispersion and
highest analyst predicted return. The input parameter is a file containing a
list of of ticker symbols (one per line), a current or historical month/year
date context for this analysis, and a portfolio size indicating the number of
recommended stocks. The output is a table sorted into deciles that includes
various target price statistics.

optional arguments:
  -h, --help            show this help message and exit
  -ticker-file TICKER_FILE
                        Ticker Symbol file
  -month MONTH          Data month
  -year YEAR            Data year
  -portfolio_size PORTFOLIO_SIZE
                        Portfolio Size
```

Examples:

```
python analyze_securities.py -ticker-file ticker-list.txt -month 6 -year 2019 -portfolio_size 3
```

where ```ticker-list.txt``` (included in the source) is a list of ticker symbols like this:

```
AAPL
AXP
BA
CAT
CSCO
CVX
...
```

## Output
```
[INFO] - 
[INFO] - Recommended Portfolio
[INFO] - {
    "portfolio_id": "ba930638-53d4-11ea-8d9d-acbc329ef75f",
    "creation_date": "2020-02-20T11:32:51.432089+00:00",
    "data_date": "2019-06-30T00:00:00",
    "strategy_name": "LOW_PRICE_DISPERSION",
    "portfolio": [
        "V",
        "KO",
        "HD"
    ]
}
[INFO] - 
[INFO] - Recommended Portfolio Return: 19.15%
[INFO] - Average Return: 10.33%
[INFO] - 
[INFO] - Analysis data
[INFO] -         analysis_price  target_price_avg  current_price  target_price_sdtdev_pct  analyst_expected_return  actual_return  decile
ticker                                                                                                                          
V               173.55        178.573200         213.31                 4.979471                 0.028944       0.229098       0
KO               50.92         51.461000          59.77                 5.915159                 0.010625       0.173802       0
HD              207.97        208.315000         243.64                 5.903079                 0.001659       0.171515       0
MRK              83.85         87.073667          82.00                 6.419469                 0.038446      -0.022063       1
MCD             207.66        210.019125         215.63                 6.755159                 0.011361       0.038380       1
WMT             110.49        111.431250         117.68                 6.635033                 0.008519       0.065074       1
CVX             124.44        138.638667         110.74                 7.163466                 0.114101      -0.110093       2
IBM             137.90        153.400000         150.86                 7.273142                 0.112400       0.093981       2
JPM             111.80        121.700000         137.49                 8.207888                 0.088551       0.229785       3
AXP             123.44        124.147000         136.93                 7.755322                 0.005727       0.109284       3
TRV             149.52        146.200000         134.51                 7.614911                -0.022204      -0.100388       3
CSCO             54.73         58.062000          46.29                 8.632152                 0.060881      -0.154212       4
VZ               57.13         58.572000          58.22                 8.632111                 0.025241       0.019079       4
PG              109.65        105.547333         125.44                 9.257142                -0.037416       0.144004       4
UNH             244.01        285.235000         305.31                 9.566147                 0.168948       0.251219       5
PFE              43.32         46.125000          36.23                 9.372358                 0.064751      -0.163666       5
BA              364.01        434.785000         338.30                10.919420                 0.194431      -0.070630       6
CAT             136.29        154.142000         136.86                11.991540                 0.130985       0.004182       6
NKE              83.95         91.594667         102.46                10.382701                 0.091062       0.220488       6
XOM              76.63         87.590500          60.34                12.462539                 0.143031      -0.212580       7
AAPL            197.92        211.690333         323.62                12.499862                 0.069575       0.635105       7
GS              204.60        238.600000         237.33                13.170997                 0.166178       0.159971       8
UTX             130.20        151.777400         150.68                12.724292                 0.165725       0.157296       8
MSFT            133.96        139.116667         187.28                12.696777                 0.038494       0.398029       8
GE               10.50         12.200000          12.61                30.860656                 0.161905       0.200952       9
INTC             47.87         53.153000          67.11                15.153425                 0.110361       0.401922       9
MMM             173.34        188.041667         159.34                13.546643                 0.084814      -0.080766       9
```

The output contains three pieces of data:
1) The selected portfolio as a JSON document
2) Selected portfolio return return vs average return
3) Processed data frame, sorted in deciles, from used to select final portfolio

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

Ran 46 tests in 0.027s

OK
Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
data_provider/intrinio_data.py                  130     38    71%
data_provider/intrinio_util.py                   27      0   100%
exception/exceptions.py                          27      1    96%
strategies/low_price_dispersion_strategy.py      62     28    55%
strategies/portfolio.py                          29      0   100%
support/financial_cache.py                       31      0   100%
support/util.py                                  11      1    91%
-----------------------------------------------------------------
TOTAL                                           317     68    79%
```

## What's next?
1) Additional Stragegies. For example a strategy that favors high price dispersion.
2) Back testing of existing strategies
3) Additional filters based on fundamentals
4) Automated trading platform