# docker container description file for SalishSeaCmd package testing environment
#
# Primarily intended for creation of a docker image for use by bitbucket-pipelines.yml.
#
# To update the image on Docker Hub:
#    docker build -t salishsea-cmd-test pipelines-test-env/
#    docker tag salishsea-cmd-test:latest douglatornell/salishsea:salishsea-cmd-test
#    docker push douglatornell/salishsea:salishsea-cmd-test

FROM continuumio/miniconda3

# Create salishsea-cmd-test conda env
ADD ./environment-test.yaml /tmp/environment-test.yaml
RUN conda env create -f /tmp/environment-test.yaml
ENV CONDA_PREFIX /opt/conda/envs/salishsea-cmd-test
# Install mercurial conda pkg
RUN conda create -n hg python=2.7
RUN conda install -n hg -c conda-forge mercurial
ENV HG /opt/conda/envs/hg/bin/hg
# Clone and install NEMO-Cmd pkg
RUN ${HG} clone https://douglatornell@bitbucket.org/salishsea/nemo-cmd /home/NEMO-Cmd
RUN ${CONDA_PREFIX}/bin/python3 -m pip install -e /home/NEMO-Cmd
