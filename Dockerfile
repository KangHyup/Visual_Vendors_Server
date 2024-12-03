# CUDA 11.3 및 CUDNN 8 기반 Devel 이미지
FROM nvidia/cuda:11.3.1-cudnn8-devel-ubuntu18.04

# 필수 패키지 설치 및 GCC 9 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    software-properties-common \
    wget \
    curl \
    ca-certificates \
    gnupg2 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    ninja-build \
    python3-dev \
    python3-pip \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc-9 g++-9 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 60 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 60 \
    && rm -rf /var/lib/apt/lists/*

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

# Conda 환경 활성화 및 CUDA 설정
ENV PATH=/opt/conda/envs/schp/bin:$PATH
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# PyTorch GPU 아키텍처 설정
ENV TORCH_CUDA_ARCH_LIST="7.5"

# 최신 pip 설치
RUN pip install --upgrade pip

# Python 패키지 설치
COPY requirements.txt /Visual_Vendors_Server/requirements.txt
RUN pip install --no-cache-dir -r /Visual_Vendors_Server/requirements.txt && \
    pip check

# 소스 코드 복사
COPY . .

# GPU가 정상적으로 작동하는지 확인용 명령어 추가
RUN python -c "import torch; print(torch.cuda.is_available())"

# 포트 개방
EXPOSE 8080

# Flask 서버 실행
CMD ["python", "server.py"]
