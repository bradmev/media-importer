#!/bin/bash

cd $2/$1 
docker build -t $1 . --no-cache
docker tag $1 150290272294.dkr.ecr.us-east-1.amazonaws.com/$1:dev
docker push 150290272294.dkr.ecr.us-east-1.amazonaws.com/$1:dev
cd ../../

aws lambda update-function-code --function-name  media-importer-$1 --image-uri 150290272294.dkr.ecr.us-east-1.amazonaws.com/$1:dev
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 150290272294.dkr.ecr.us-east-1.amazonaws.com
