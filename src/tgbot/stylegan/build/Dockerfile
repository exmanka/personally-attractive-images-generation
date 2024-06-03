FROM python:3.10-slim

WORKDIR /usr/src/stylegan

COPY ./build/requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./dep/* /usr/local/lib/python3.10/site-packages

CMD [ "python", "./main.py"]