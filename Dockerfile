FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "FA-1.py", "--server.port=8501", "--server.address=0.0.0.0"]