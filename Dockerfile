FROM python:3.9-alpine

WORKDIR /

COPY WechatImageDecoder.py /WechatImageDecoder.py

ENTRYPOINT ["python", "/WechatImageDecoder.py"]
