FROM ubuntu:latest


# Install Open3D system dependencies and pip
RUN apt-get update && apt-get install --no-install-recommends -y \
    libgl1 \
    libgomp1 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Open3D from the PyPI repositories
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --upgrade open3d


# FROM python:3.10-slim
# COPY --chmod=555 ./bin/* /usr/local/bin/

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

WORKDIR /app

COPY brefv_spec/ brefv_spec/

COPY main.py main.py

CMD ["python3", "main.py"]
