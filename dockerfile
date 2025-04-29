FROM python:3.9-slim

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 생성
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY src/ ./src/
COPY main/ ./main/
COPY project_siren.py .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 볼륨 설정 (데이터 저장을 위한 디렉토리)
VOLUME ["/data"]

# 사용 방법 안내
ENTRYPOINT ["python", "project_siren.py"]