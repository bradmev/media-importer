#!/bin/bash

cd $1/$2
docker build -t $2 . --no-cache
cd ../../
# docker run -p 9000:8080 -v $PWD/$1/$2/app.py:/var/task/app.py $2

docker run -p 9000:8080 --mount type=bind,source="$(pwd)"/$1/$2/app.py,target=/var/task/app.py  $2

# trigger

# curl --request POST \                                                                                                                      
#   --url http://localhost:9000/2015-03-31/functions/function/invocations \
#   --header 'Content-Type: application/json' \
#   --data '
#   {
#       "access_token": "ya29.a0Ael9sCO-0fjsyjR11J11rR7Ngc2-BOOrY5oi10N9ri928QFpGWZnZ6fma_CNLFSUWr2Qz8JxeaAwE8YdNTcy5OJa4pbiPED1cY7Hg1g4JhlXS7boZcJfjDt7uBUjFrgXoII3OfrtAWqX2WfgwDfbCfL4RlVHGgaCgYKAaQSARISFQF4udJhG83SLDQ7dZHB7ZITV0hs0w0165",
#       "album_id": "AOPR9OFrXMHxxvf-EjKKTPB6IwW8SMW6HIScXM3POiGc5P4gpaGcW_zWFNtYN8qMH287z2ygWETK"
#   }'