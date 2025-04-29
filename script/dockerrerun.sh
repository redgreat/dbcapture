#!/bin/bash

docker stop dbcapture
docker rm dbcapture
docker rmi registry.cn-hangzhou.aliyuncs.com/redgreat/dbcapture
docker-compose up -d
