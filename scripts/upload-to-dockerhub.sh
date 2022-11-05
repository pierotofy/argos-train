#!/bin/bash
sudo docker login -u argosopentech
sudo docker build -t argostrain .
sudo docker image tag argostrain argosopentech/argostrain:latest
sudo docker image push argosopentech/argostrain:latest
