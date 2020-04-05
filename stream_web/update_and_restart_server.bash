git pull 
docker stop $(docker ps -q --filter ancestor=pinellolab/stream_web)
docker run -p 10001:10001 \
-v /Volumes/Data/STREAM/precomputed/:/stream_web/precomputed \
-v /Volumes/Data/STREAM/UPLOADS_FOLDER:/tmp/UPLOADS_FOLDER \
-v /Volumes/Data/STREAM/RESULTS_FOLDER:/tmp/RESULTS_FOLDER \
-d -it pinellolab/stream_web 
#-v /Volumes/Data/STREAM/precomputed/:/stream_web/precomputed

#-v /Volumes/pinello/PROJECTS/2016_12_STREAM/STREAM_web/precomputed/:/precomputed

#-v /Volumes/Data/STREAM/UPLOADS_FOLDER:/tmp/UPLOADS_FOLDER \
#-v /Volumes/Data/STREAM/RESULTS_FOLDER:/tmp/RESULTS_FOLDER \

#-v /Volumes/Data/STREAM/tmp:/tmp \
#-v /Volumes/Data/STREAM_DB_top_15/:/STREAM/precomputed \

#-v /Users/sailor/Projects/STREAM/STREAM:/STREAM \

