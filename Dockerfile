# Ubuntu 18.04 베이스 이미지
FROM ubuntu:18.04

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    ca-certificates \
    gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# Miniconda 설치
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh && \
    /opt/conda/bin/conda clean -t -i -p -y

# Miniconda 경로 추가
ENV PATH=/opt/conda/bin:$PATH

# 작업 디렉토리 설정
WORKDIR /Visual_Vendors_Server

# Conda 환경 생성
COPY environment.yaml /Visual_Vendors_Server/environment.yaml
RUN conda env create -f /Visual_Vendors_Server/environment.yaml && \
    conda clean -afy

# Conda 환경 활성화
ENV PATH /opt/conda/envs/schp/bin:$PATH

# 최신 pip 설치
RUN /opt/conda/bin/pip install --upgrade pip

# Python 패키지 설치
COPY requirements.txt /Visual_Vendors_Server/requirements.txt
RUN /opt/conda/envs/schp/bin/pip install --no-cache-dir -r /Visual_Vendors_Server/requirements.txt && \
    /opt/conda/envs/schp/bin/pip check

# 소스 코드 복사
COPY . .

# 포트 개방
EXPOSE 8080

# Flask 서버 실행
CMD ["python", "server.py"]
