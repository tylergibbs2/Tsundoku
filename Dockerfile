FROM nikolaik/python-nodejs:python3.8-nodejs18
LABEL maintainer="Tyler Gibbs <gibbstyler7@gmail.com>"

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get install -y ffmpeg

ENV IS_DOCKER 1

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

RUN yarn
RUN yarn build

EXPOSE 6439
CMD [ "python", "-m", "tsundoku" ]