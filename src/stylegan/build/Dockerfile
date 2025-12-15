FROM nvcr.io/nvidia/pytorch:21.08-py3

WORKDIR /usr/src/stylegan

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./build/requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./dep/ /opt/conda/lib/python3.8/site-packages/

CMD [ "python", "./main.py"]