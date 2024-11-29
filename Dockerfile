# 베이스 이미지로 CUDA 지원 Python 이미지 선택
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# 작업 디렉토리 설정
WORKDIR /YOLO_Server

# 시스템 종속성 설치
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ninja-build \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN chmod +x cuda_11.8.0_520.61.05_linux.run
RUN sudo ./cuda_11.8.0_520.61.05_linux.run

# Python 패키지 종속성 복사 및 설치 (변동성이 적은 requirements.txt 먼저 설치)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사 (변동성이 큰 소스코드 마지막에 복사)
COPY . .

# Flask 서버 실행 포트 설정
EXPOSE 8080

# 일반 사용자 권한 설정 (보안 강화)
RUN groupadd -r yolo_group && useradd -r -g yolo_group yolo_user
USER yolo_user

# Flask 서버 실행
CMD ["python3", "server.py"]
