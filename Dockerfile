FROM python:3.8-alpine
RUN apk add  --no-cache ffmpeg
RUN mkdir /app
RUN mkdir /app/watchFolder
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python","-u","subExtractor.py"]