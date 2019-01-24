############################################################
# Dockerfile to build STREAM webapp
############################################################

# Set the base image to stream
FROM pinellolab/stream_bioconda

# File Author / Maintainer
MAINTAINER Huidong Chen

#website dependencies
RUN pip install dash==0.21.0  # The core dash backend
RUN pip install dash-renderer==0.11.3  # The dash front-end
RUN pip install dash-html-components==0.9.0  # HTML components
RUN pip install dash-core-components==0.21.1  # Supercharged components
RUN pip install plotly --upgrade  # Plotly graphing library used in examples
RUN pip install gunicorn

#RUN apt-get install unzip 
#libxml2 libxml2-dev -y

# install zips
#RUN apt-get update && apt-get install zip -y

# create environment
COPY stream_web /stream_web

# upload button
COPY /stream_web/upload-button.zip /
RUN unzip upload-button.zip && cd upload-button && python setup.py install
RUN rm upload-button.zip
RUN rm -Rf upload-button

COPY /stream_web/static/STREAM.css /opt/conda/lib/python3.6/site-packages/dash_core_components/
COPY /stream_web/static/Loading-State.css /opt/conda/lib/python3.6/site-packages/dash_core_components/
COPY /stream_web/static/jquery-3.3.1.min.js /opt/conda/lib/python3.6/site-packages/dash_core_components/
RUN mkdir /tmp/UPLOADS_FOLDER
RUN mkdir /tmp/RESULTS_FOLDER


WORKDIR /stream_web/

EXPOSE 10001
#CMD ["bash", "/stream_web/start_server_docker.sh"]

# Enable the STREAM webapp
ENTRYPOINT ["bash", "/stream_web/start_server_docker.sh"]
