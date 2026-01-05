FROM ubuntu:24.04
LABEL authors=jsamis

WORKDIR /src

RUN apt update && apt upgrade --no-recomends-install \
    ca-certificates \
    python3 \
    python3-dotenv \
    python3-venv \


RUN python -m pip install --upgrade pip

COPY . .




ENTRYPOINT ["python"]










