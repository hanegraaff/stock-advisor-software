docker build -f Dockerfile.rec_svc -t stock-advisor/recommendation-svc:v1.0.0 .
docker build -f Dockerfile.pfolio_man -t stock-advisor/portfolio-manager:v1.0.0 .