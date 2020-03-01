# Overview
A program that makes stock recommendations depending on the level of analyst target price agreement. It is based on the findings of paper like these:

https://www8.gsb.columbia.edu/faculty-research/sites/faculty-research/files/FRANK%20ZHANG%20PAPER%20PSZ_20190913.pdf

https://editorialexpress.com/cgi-bin/conference/download.cgi?db_name=SWFA2019&paper_id=80

http://www.fmaconferences.org/Vegas/Papers/DspJanuary2016.pdf


They suggest, among other things, that when taken individually or even on average, analyst price targets are not a good predictor of returns, relative agreement or disagreement is. 

The code presented here is based one the ```security-valuator``` project

https://github.com/hanegraaff/security-valuator


## Algorithm Description

Given a time period and list of ticker symbols:

1) Download analyst target price information: the average target price, the standard deviation of the price dispersion and latest price for the seleted time period.

2) Compute the standard deviation to a percentage and sort all stocks into deciles ranked by that percentage.

3) Select a portfolio from the last decile. This will return stocks with the largest level of disagreement.



## Release Notes (v0.4)
This is an early version with limited functionality.

* Back test
* Ability to perform MMT on a dataframe to compute current or historical returns.

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
src >>python generate_portfolio.py -h

usage: generate_portfolio.py [-h] [-ticker-file TICKER_FILE]
                             [-analysis_month ANALYSIS_MONTH]
                             [-analysis_year ANALYSIS_YEAR]
                             [-price_date PRICE_DATE]
                             [-portfolio_size PORTFOLIO_SIZE]

Generate a portfolio recommendation given a list of ticker symbols. Selection
is based on on the degree of analyst target price agreement, specifically it
will select stocks with the lowest agreement and highest predicted return. The
input parameters are a file containing a list of of ticker symbols, the period
for the recommendations, a price date used to show actual returns and the size
of the final portfolio selection. The output is a data structure with the
selection, and a data frame showing the underlining stock ranking.

optional arguments:
  -h, --help            show this help message and exit
  -ticker-file TICKER_FILE
                        Ticker Symbol file
  -analysis_month ANALYSIS_MONTH
                        Analysis period's month
  -analysis_year ANALYSIS_YEAR
                        Analysis period's year
  -price_date PRICE_DATE
                        Current Price Date (YYYY/MM/DD)
  -portfolio_size PORTFOLIO_SIZE
                        Selected Portfolio Size
```

Examples:

```
python generate_portfolio.py -ticker-file ticker-list.txt -analysis_year 2019 -analysis_month 6 -price_date 2020/02/29 -portfolio_size 3
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

```analysis_year``` / ```analysis_month``` represent the financial period used to make a recommendation, and ```price_date``` is the price date used to calculate the portfolio's current returns.

The example above will generate a portfolio recommendation as of 06/2019 and display the return as of 2020/02/29


## Output
```
[INFO] - 
[INFO] - Recommended Portfolio
[INFO] - {
    "portfolio_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
    "creation_date": "2020-03-01T04:56:57.612693+00:00",
    "data_date": "2019-08-31T00:00:00",
    "strategy_name": "PRICE_DISPERSION",
    "portfolio": [
        "GE",
        "INTC",
        "AAPL"
    ]
}
[INFO] - 
[INFO] - Recommended Portfolio Return: 19.49%
[INFO] - Average Return: 4.77%
[INFO] - 
[INFO] - Analysis Period - 8/2019, Actual Returns as of: 2019/10/30
analysis_period ticker  dispersion_stdev_pct  analyst_expected_return  actual_return  decile
         2019-8     GE                30.652                    0.470          0.225       9
         2019-8   INTC                15.420                    0.136          0.194       9
         2019-8   AAPL                14.518                    0.063          0.165       9
         2019-8    UTX                13.414                    0.191          0.104       8
         2019-8    MMM                12.581                    0.116          0.041       8
         2019-8     PG                13.586                   -0.050          0.039       8
         2019-8    PFE                12.527                    0.246          0.082       7
         2019-8     GS                11.635                    0.223          0.058       7
         2019-8    CAT                10.072                    0.220          0.179       6
         2019-8     BA                 9.590                    0.184         -0.050       6
         2019-8   MSFT                10.812                    0.093          0.049       6
         2019-8    XOM                 8.444                    0.222         -0.011       5
         2019-8    NKE                 9.515                    0.102          0.067       5
         2019-8    UNH                 7.894                    0.248          0.089       4
         2019-8   CSCO                 8.093                    0.218          0.016       4
         2019-8    WMT                 8.045                   -0.007          0.034       4
         2019-8    IBM                 7.586                    0.157         -0.002       3
         2019-8    AXP                 7.826                    0.094         -0.019       3
         2019-8    MCD                 7.857                    0.021         -0.097       3
         2019-8    MRK                 7.522                    0.040         -0.003       2
         2019-8    TRV                 7.433                    0.038         -0.117       2
         2019-8    JPM                 7.262                    0.113          0.144       1
         2019-8     VZ                 6.668                    0.043          0.046       1
         2019-8     HD                 6.855                   -0.051          0.037       1
         2019-8    CVX                 5.515                    0.171         -0.012       0
         2019-8    JNJ                 5.205                    0.160          0.035       0
         2019-8      V                 5.398                    0.095         -0.009       0
```

The output contains three pieces of data:
1) The selected portfolio as a JSON document
2) Selected portfolio return return vs average return
3) Processed data frame, sorted in deciles, from used to select final portfolio

The ```dispersion_stdev_pct``` column represents the degree of analyst agreement, lower values indicate higher agreement, and is expressed as as the standard deviation percentage (from the mean).

The ```decile``` column shows the relative ranking for this ticker.

## Backtesting

It is possible to backtest this strategy by running the ```price_dispersion_backtest.py``` script. It works by running the strategy from 05/2019 to 11/2019 and comparing the returns of the selected portfolio with the average of the list supplied to it.

Example:

```python price_dispersion_backtest.py -ticker-file ticker-list.txt -portfolio-size 3```

```
investment_period  ticker_sample_size  avg_ret_1M  sel_ret_1M  avg_ret_2M  sel_ret_2M  avg_ret_3M  sel_ret_3M
          2019/05                  12       8.09%       9.95%      11.17%      12.31%       8.74%       5.49%
          2019/06                  27       2.41%       3.56%      -1.95%     -10.78%       0.54%      -4.30%
          2019/07                  27      -3.08%      -9.93%      -0.92%      -3.65%       0.17%       1.51%
          2019/08                  27       2.85%       8.12%       4.77%      19.49%       7.34%      29.03%
          2019/09                  23       2.26%       9.60%       4.80%      17.53%       8.21%      21.29%
          2019/10                  28       2.67%       5.34%       4.99%       5.97%       6.43%      14.98%
          2019/11                  26       2.26%       0.68%       3.53%       8.88%      -8.55%      -7.02%
investment_period ticker_sample_size  avg_tot_1M  sel_tot_1M  avg_tot_2M  sel_tot_2M  avg_tot_3M  sel_tot_3M
          ----/--                 --      17.45%      27.30%      26.39%      49.74%      22.89%      60.98%
```

Each line reports the returns for each montly portfolio selection at a 1 month, 2 month and 3 month horizon.

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

Ran 50 tests in 0.036s

OK
Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
data_provider/intrinio_data.py                  131     39    70%
data_provider/intrinio_util.py                   27      0   100%
exception/exceptions.py                          27      1    96%
strategies/calculator.py                         19      0   100%
strategies/price_dispersion_strategy.py          65     26    60%
strategies/portfolio.py                          29      0   100%
support/financial_cache.py                       31      0   100%
support/util.py                                  11      1    91%
-----------------------------------------------------------------
TOTAL                                           340     67    80%
```

## What's next?
1) Additional Stragegies. For example a strategy that favors high price dispersion.
2) Automated trading platform