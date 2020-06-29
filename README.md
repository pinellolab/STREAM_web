# STREAM_web
STREAM interactive website [stream.pinellolab.org](https://stream.pinellolab.partners.org/)


STREAM interactive website
--------------------------

In order to make STREAM user friendly and accessible to non-bioinformatician, we have created an interactive website: [http://stream.pinellolab.org](https://stream.pinellolab.partners.org/) 

The website implements the features of **stream command line** and in addition provides interactive and exploratory panels to visualize single-cell trajectories.  

The website offers two functions: 

1) To run STREAM on single-cell transcriptomic or epigenomic data provided by the users.  
2) The first interactive database of precomputed trajectories with results for seven published datasets. The users can visualize and explore cells’ developmental trajectories, subpopulations and their gene expression patterns at single-cell level. 

**Note: The website can also run on a local machine using the provided Docker image we have created.** 


Installation with Docker
------------------------

Docker can be downloaded freely from here: [https://store.docker.com/search?offering=community&type=edition](https://store.docker.com/search?offering=community&type=edition)

To get an image of STREAM_web, simply execute the following command:

```sh
$ docker pull pinellolab/stream_web
```

To run the website on a local machine after the Docker installation, from the command line execute the following command:
```sh
$ docker run -p 10001:10001 pinellolab/stream_web
```

After the execution of the command the user will have a local instance of the website accessible at the URL: 
[http://localhost:10001](http://localhost:10001)

To stop the website, from the command line execute the following command:
```sh
$ docker ps
$ docker kill CONTAINER_ID
```
