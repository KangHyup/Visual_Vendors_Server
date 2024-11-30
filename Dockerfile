FROM nvidia/cuda:10.1-cudnn7-runtime-ubuntu18.04

# Miniconda 설치
RUN apt-get update && apt-get install -y wget && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh && \
    /opt/conda/bin/conda clean -tipsy

# Conda 경로 추가
ENV PATH=/opt/conda/bin:$PATH

# 작업 디렉토리 설정
WORKDIR /Visual_Vendors_Server

# 환경 설정 파일 복사
COPY environment.yaml /Visual_Vendors_Server/environment.yaml

# Conda 환경 생성 및 활성화
RUN conda env create -f /Visual_Vendors_Server/environment.yaml && \
    conda clean -afy

# Conda 환경 활성화
ENV PATH /opt/conda/envs/schp/bin:$PATH

# 소스 코드 복사
COPY . .

# Flask 서버 실행
CMD ["python", "server.py"]
