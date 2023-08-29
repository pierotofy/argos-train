FROM ubuntu

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y sudo vim

RUN useradd -ms /bin/bash argosopentech
RUN passwd -d argosopentech
RUN echo "argosopentech ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/argosopentech
RUN usermod -aG sudo argosopentech

ADD . / /home/argosopentech/argos-train/
RUN chown -R argosopentech:argosopentech /home/argosopentech/argos-train
USER argosopentech
WORKDIR /home/argosopentech/argos-train
RUN chmod +x /home/argosopentech/argos-train/bin/* && /home/argosopentech/argos-train/bin/argos-train-init

ENTRYPOINT ["/bin/bash"]

#ENTRYPOINT ["/home/argosopentech/bin/python", "/home/argosopentech/argos-train/bin/argos-train"]
