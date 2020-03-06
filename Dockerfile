FROM python:3.8-slim-buster
LABEL maintainer hanegraaff@gmail.com
COPY ./src /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "generate_portfolio.py"]
