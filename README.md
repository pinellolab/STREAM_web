# STREAM_web
STREAM interactive website [stream.pinellolab.org](http://stream.pinellolab.org/)

Installation with Docker
------------------------

With Docker no installation is required, the only dependence is Docker itself. Users will completely get rid of all the installation and configuration issues. Docker will do all the dirty work for you!

Docker can be downloaded freely from here: [https://store.docker.com/search?offering=community&type=edition](https://store.docker.com/search?offering=community&type=edition)

To get an image of STREAM_web, simply execute the following command:

```sh
$ docker pull pinellolab/stream_web
```


Basic usage of *docker run* 

```sh
$ docker run [OPTIONS] IMAGE [COMMAND] [ARG...]
```

OPTIONS:  
```
--publish , -p	Publish a container’s port(s) to the host  
--volume , -v	Bind mount a volume  
--workdir , -w	Working directory inside the container  
```

STREAM interactive website
--------------------------

In order to make STREAM user friendly and accessible to non-bioinformatician, we have created an interactive website: [http://stream.pinellolab.org](http://stream.pinellolab.org) The website implements all the features of the command line version and in addition provides interactive and exploratory panels to zoom and visualize single-cells on any given branch.

The website offers two functions: 1) To run STREAM on single-cell transcriptomic or epigenomic data provided by the users. 2) The first interactive database of precomputed trajectories with results for seven published datasets. The users can visualize and explore cells’ developmental trajectories, subpopulations and their gene expression patterns at single-cell level. 

The website can also run on a local machine using the provided Docker image we have created. To run the website in a local machine after the Docker installation, from the command line execute the following command:
```sh
$ docker run -p 10001:10001 pinellolab/stream_web
```

After the execution of the command the user will have a local instance of the website accessible at the URL: 
[http://localhost:10001](http://localhost:10001)