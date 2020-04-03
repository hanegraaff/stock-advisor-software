# Overview
![Stock Advisor Design](doc/stock-advisor.png)

The Securities Recommendation service is a component of the Stock Advisor system that generates monthly US Equities recommendations using a market sentiment algorythm that ranks stocks the level of analyst target price agreement. It is based on the findings of paper like these:

|Paper|Author(s)|
|--|--|
|[Consensus Analyst Target Prices: Information Content and Implications for Investors](doc/Consensus-Analyst-Target-Prices.pdf)|Asa B. Palley, Thomas D. Steffen, X. Frank Zhang|
|[Dispersion in Analysts’ Target Prices and Stock Returns](doc/Dispersion-Analysts-Target-Prices-Stock-Returns.pdf)|Hongrui Feng Shu Yan|
|[The predictive power of analyst price target and its dispersion](doc/Predictive-Power-Analyst-Price-Target-Dispersion.pdf)|Heng(Emily) Wang, Shu Yan|

They suggest, among other things, that when taken individually or even on average, analyst price targets are not a good predictor of returns, but the degree of agreement/disagreement is.

This repo is part of the Stock Advisor project found here:

https://github.com/hanegraaff/stock-advisor-main-project

## Algorithm Description
The algorithm reads a list of ticker symbols and downloads various financial data points. It then ranks each security into deciles, with the lowest decile containing stocks with the highest level of analyst price agreement and the highest decile containing stocks with the lowest price agreement. It then sorts each decile by expected returns, and returns a subset of the list. The number of securities that are returned are specified in the command using the ```-output-size``` option.

These are the specific steps:

1) Download financial data for each symbol:
    - Current Price
    - Analyst price forecast average
    - Analyst price forecast standard deviation
    - Analyst price forecast count (i.e. total forecasts)
2) Normalize the standard deviation by converting it into a relative percentage.
3) Rank the portfolio by this percentage and sort into deciles.
4) Select a subset from the last decile. This will return stocks with the largest level of disagreement.

## Financial Data
This program relies on financial data to perform its calculations, specifically it requires current and historical pricing information as well as analyst target price predictions. This data is sourced from Intrinio, though other providers could be used.

Intrinio offers free access to their sandbox, which gives developers access to a limited dataset comprising of the DOW30, and the results presented here are based on that list. A paid subscription allows access to a much larger universe of stocks.


## Release Notes (v0.7)
This is an initial version that offers the following features

* Ability to rank securities and generate recommendation.
* Local caching of financial data
* Back testing capability
* Ability to run inside a Docker container
* Integrate into Stock Advisor Infrastructure, specifically ECS.

## Prerequisites
### API Keys
An API Key for the Intrinio (https://www.intrinio.com) with access to the "US Fundamentals and Stock Prices" and "Zacks Price Targets" feeds

the API must be saved to the environment like so:

```export INTRINIO_API_KEY=[your API key]```

### Installation requirements
```pip install -r requirements.txt```

It is highly recommended to run this in a virtual environment:

```
python3 -m venv venv
source venv/bin/activate

cd src
pip install -r requirements.txt
```

## Running the service from the command line
All scripts must be executed from the ```src``` folder.

```
src >>python stock_recommendation_svc.py -h
usage: stock_recommendation_svc.py [-h] -ticker_file TICKER_FILE -output_size
                                   OUTPUT_SIZE
                                   {test,production} ...

Reads a list of US Equity ticker symbols and recommends a subset of them based
on the degree of analyst target price agreement, specifically it will select
stocks with the lowest agreement and highest predicted return. The input
parameters consist of a file with a list of of ticker symbols, and the month
and year period for the recommendations. The output is a JSON data structure
with the final selection. When running this script in "production" mode, the
analysis period is determined at runtime, and the system will interact with the AWS
infrastructure to read inputs and store outputs.

optional arguments:
  -h, --help            show this help message and exit
  -ticker_file TICKER_FILE
                        Ticker Symbol local file path
  -output_size OUTPUT_SIZE
                        Number of selected securities

environment:
  runtime environment

  {test,production}     the runtime environment of the application. It can be
                        either "test" or "production"
    test                Test mode. Analysis period and current date must be
                        passed explicitly
    production          Production mode. Analysis period and current date are
                        determined at runtime
```

Where ```-ticker_file``` represents a local file or s3 object used to represent the universe of stocks that will be considered. It must contain
a single ticker symbol per line.

```
AAPL
AXP
BA
CAT
CSCO
CVX
...
```

and ```-output_size``` represents the the total number of recommended
stocks resulting from the analysis.

The script can be run in two modes, representing different runtime environments.

### Production mode
**Production** mode will automatically determine the analysis period based on the calendar date, and display actual returns using the same. It will also use S3 to read the input ticker file and store results. This is the mode that must be used when running in ECS.

In this mode the service will identify the appropriate AWS infrastructure using a combination of CloudFormation exports and a namespace suppled to the command line (```-app_namespace```) used to avoid collisions. So for example, if the application namespace is set to ```sa```, the S3 bucket will be identified using the ```sa-data-bucket-name``` export. These are defined in the ```support.constants``` module.

```
src >>python stock_recommendation_svc.py production -h
usage: stock_recommendation_svc.py production [-h] -app_namespace
                                            APP_NAMESPACE

optional arguments:
-h, --help            show this help message and exit
-app_namespace APP_NAMESPACE
                        Application namespace used to identify AWS resources
```

For example:
```
python stock_recommendation_svc.py -ticker_file djia30.txt -output_size 3 production -app_namespace sa
```

This example generates a 3 stock recommendation using the DOW30 as an input, and using the latest analysis period based on calendar date.

### Test mode
**Test** mode expects the analysis period to be supplied using the command line, and will not interact with AWS, but rather rely on local resources. This mode is used when running and testing outside the production environment, and may also be used to run historically.

In this mode, ```-price_date``` is optional, and is used to determine the price date used to display the current returns of the selection.
    
```
src >>python stock_recommendation_svc.py test -h
usage: stock_recommendation_svc.py test [-h] -analysis_month ANALYSIS_MONTH
                                        -analysis_year ANALYSIS_YEAR
                                        [-price_date PRICE_DATE]

optional arguments:
  -h, --help            show this help message and exit
  -analysis_month ANALYSIS_MONTH
                        Analysis period's month
  -analysis_year ANALYSIS_YEAR
                        Analysis period's year
  -price_date PRICE_DATE
                        Price Date (YYYY/MM/DD) used to compute current
                        returns

```

For example:
```
python stock_recommendation_svc.py -ticker_file djia30.txt -output_size 3 test -analysis_year 2020 -analysis_month 1 -price_date 2020/03/01 
```

This will generate a 3 stock recommendation using a local ticker file of the DOW 30 using an analysis period of 01/2020 and a price date of 03/01

```analysis_year``` / ```analysis_month``` represent the financial period of the analyst forecasts, and ```price_date``` is the price date used to calculate the portfolio's current returns.


## Running the service as a docker image
It is possible to package the application as a Docker image. To build the container, run the following script:

```
>>./docker_build.sh
Sending build context to Docker daemon    126MB
Step 1/6 : FROM python:3.8-slim-buster
 ---> ee07b1466448
Step 2/6 : LABEL maintainer hanegraaff@gmail.com
 ---> Running in a684be7d3a89
Removing intermediate container a684be7d3a89
 ---> fa1bfe7dedbb
Step 3/6 : COPY ./src /app
 ---> 2b4972cee31b
Step 4/6 : WORKDIR /app
 ---> Running in cc780c1aca64
Removing intermediate container cc780c1aca64
 ---> 2c9d26ea0a28
Step 5/6 : RUN pip install -r requirements.txt
 ---> Running in 8e6d18a64ef7
...
Removing intermediate container 8e6d18a64ef7
 ---> b166ecddc400
Step 6/6 : ENTRYPOINT ["python", "recommendation_svc.py"]
 ---> Running in 3963296f1b3f
Removing intermediate container 3963296f1b3f
 ---> f1a79df20439
Successfully built f1a79df20439
Successfully tagged stock-advisor/recommendation_svc:v1.0.0
```
The resulting image will look like this:
```
>>docker images
REPOSITORY                         TAG                 IMAGE ID            CREATED             SIZE
stock-advisor/generate-portfolio   v1.0.0              f1a79df20439        9 hours ago         376MB
python                             3.8-slim-buster     ee07b1466448        7 days ago          193MB
```

Once built, the container is executed in a similar way as the script. Note how the ```INTRINIO_API_KEY``` must be supplied as a special environment variable. AWS credentials must also be supplied externally, in a similar way.

For example:

```
docker run -e INTRINIO_API_KEY=xxx image-id -ticker_file djia30.txt -output_size 3 production -app_namespace sa
```

## Running the service in ECS
This service is intended to be run in ECS using a Fargate task. The automation contained in the (Stock Advisor) main project will create the ECS Cluster, task definition, Container Repository and CodeBuild project needed to build and deploy the service to AWS.

More documentation will follow

## Output

The main output is a JSON Document with the portfolio recommendation.

```
[INFO] - 
[INFO] - Recommended Securities
[INFO] - {
    "set_id": "fbd886d6-75a8-11ea-ad82-acbc329ef75f",
    "creation_date": "2020-04-03T12:45:22.844743+00:00",
    "analysis_start_date": "2019-08-01T00:00:00",
    "analysis_end_date": "2019-08-31T00:00:00",
    "price_date": "2019-08-31T04:00:00+00:00",
    "strategy_name": "PRICE_DISPERSION",
    "security_type": "US Equities",
    "security_set": {
        "GE": 8.25,
        "INTC": 47.41,
        "AAPL": 208.74
    }
}
```
Additionally, the program will display a Pandas Data Frame containing the ranked stocks used to select the final portfolio, and an indication of its relative performance compared to the average of all all supplied stocks.
```
[INFO] - 
[INFO] - Recommended Securities Return: 19.49%
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

Each line reports the returns for each montly portfolio selection at a 1 month, 2 month and 3 month horizon.

## Caching of financial data
All financial data is saved to a local cache to reduce throttling and API limits when using the Intrinio API. As of this version the data is set to never expire, and the cache will grow to a maximum size of 4GB.

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
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.056s

OK
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
cloud/aws_service_wrapper.py                 60     10    83%
data_provider/intrinio_data.py              142     47    67%
data_provider/intrinio_util.py               27      0   100%
exception/exceptions.py                      30      1    97%
model/recommendation_set.py                  54      5    91%
model/ticker_file.py                         50     10    80%
service_support/recommendation_svc.py        29      3    90%
strategies/calculator.py                     19      0   100%
strategies/price_dispersion_strategy.py      68     29    57%
support/constants.py                         11      0   100%
support/financial_cache.py                   33      2    94%
support/util.py                              11      1    91%
-------------------------------------------------------------
TOTAL                                       534    108    80%
```