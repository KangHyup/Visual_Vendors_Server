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

# NVIDIA 리포지토리 추가 및 CUDA 10.1 설치
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-ubuntu1804.pin -O /etc/apt/preferences.d/cuda-repository-pin-600 && \
    wget https://developer.download.nvidia.com/compute/cuda/10.1/Prod/local_installers/cuda-repo-ubuntu1804-10-1-local-10.1.243-418.87.00_1.0-1_amd64.deb && \
    dpkg -i cuda-repo-ubuntu1804-10-1-local-10.1.243-418.87.00_1.0-1_amd64.deb && \
    apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    cuda-10-1 && \
    rm -rf /var/lib/apt/lists/*

# cuDNN 설치
RUN apt-get install -y --no-install-recommends \
    libcudnn7 \
    libcudnn7-dev && \
    rm -rf /var/lib/apt/lists/*

# 환경 변수 설정
ENV PATH=/usr/local/cuda-10.1/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda-10.1/lib64:$LD_LIBRARY_PATH

# Miniconda 설치
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh && \
    /opt/conda/bin/conda clean -tipsy

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

# 소스 코드 복사
COPY . .

# Flask 서버 실행
CMD ["python", "server.py"]
