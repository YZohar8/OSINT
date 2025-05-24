FROM python:3.11-slim

WORKDIR /app

# install tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    jq \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# inatall Amass
# -------------------------
RUN wget https://github.com/OWASP/Amass/releases/download/v3.21.0/amass_linux_amd64.zip && \
    unzip amass_linux_amd64.zip && \
    mv amass_linux_amd64/amass /usr/local/bin/amass && \
    chmod +x /usr/local/bin/amass && \
    rm -rf amass_linux_amd64*

# -------------------------------
# install theHarvester from GitHub
# -------------------------------
RUN git clone https://github.com/laramies/theHarvester.git /opt/theHarvester && \
    pip install /opt/theHarvester

RUN ln -sf /usr/local/bin/theHarvester /usr/local/bin/theharvester

ENV PATH="/usr/local/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
