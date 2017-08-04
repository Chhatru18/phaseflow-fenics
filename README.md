# phaseflow-fenics
Phaseflow simulates the unsteady conservation of mass, momentum, and energy for an incompressible fluid using the Python finite element library FEniCS.

Currently only a homogeneous fluid is supported. The project is currently under heavy development to support phase-change materials, particularly the melting and freezing of water-ice.

Author: Alexander G. Zimmerman <zimmerman@aices.rwth-aachen.de>

[![Build Status](https://travis-ci.org/geo-fluid-dynamics/phaseflow-fenics.svg?branch=master)](https://travis-ci.org/geo-fluid-dynamics/phaseflow-fenics) (<b>Continuous integration status</b>; click the button to go to Travis-CI)

## Current capabilities
- Incompressible Navier-Stokes (steady and unsteady), lid-driven cavity benchmark
- Natural convection, where the momentum equation includes temperature-based bouyancy forces per the Boussinesq approximation

# For users:
## [Docker](https://www.docker.com)

We have a [Docker image](quay.io/fenicsproject/stable:latest) with a pre-configured Python environment and pre-built FEniCS, courtesy of the FEniCS developers.

Get the [free community edition of Docker](https://www.docker.com/community-edition).

Pull the [image](docker run -ti quay.io/fenicsproject/stable:current) and run the container with Docker

    docker run -ti quay.io/fenicsproject/stable:current
    
Or run the container with access to a shared folder (shared between the host and the container)

    docker run -ti -v $(pwd):/home/fenics/shared quay.io/fenicsproject/stable:current
    
Note that our [Docker image](https://hub.docker.com/r/zimmerman/phaseflow-fenics/latest) only adds pytest to the [FEniCS Docker image](quay.io/fenicsproject/stable:latest) and clones this repository, as shown in our [Dockerfile](https://github.com/alexanderzimmerman/phaseflow-fenics/blob/master/Dockerfile). So for the most part, everything you need to know is [here in the "FEniCS in Docker" manual](https://fenics.readthedocs.io/projects/containers/en/latest/).

If you plan to use this container repeatedly, then instead use this command to also give it a name

    docker run -ti -v $(pwd):/home/fenics/shared --name fenics quay.io/fenicsproject/stable:current

After exiting the container, you can start it again with

    docker start fenics
    
You can confirm that the container is running with

    docker ps
    
or list all containers (running or not) with

    docker ps -a

To enter a bash terminal inside of the running container

    docker start fenics
    
    docker exec -ti -u fenics fenics /bin/bash -l
    
## Run phaseflow in Docker

    docker run -ti quay.io/fenicsproject/stable:current
    
    git clone git@github.com:geo-fluid-dynamics/phaseflow-fenics.git
    
    cd phaseflow-fenics
    
    python -m pytest
    
# For developers:
## Project structure
This project mostly follows the structure suggested by [The Hitchhiker's Guide to Python](https://python-guide-pt-br.readthedocs.io/en/latest/writing/structure/)
