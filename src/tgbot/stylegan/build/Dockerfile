FROM nvcr.io/nvidia/pytorch:21.08-py3

WORKDIR /usr/src/stylegan

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install imageio imageio-ffmpeg==0.4.4 pyspng==0.1.0 numpy fastapi[all]

COPY . .
COPY ./dep/ /opt/conda/lib/python3.8/site-packages/

CMD [ "python", "./main.py"]