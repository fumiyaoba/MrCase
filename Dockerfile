FROM python:3.13-slim

WORKDIR /work

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# デフォルトは python 実行にしておく（run時にスクリプトを指定できる）
CMD ["python"]
