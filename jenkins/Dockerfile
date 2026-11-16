FROM jenkins/jenkins:lts-jdk21

USER root
# Software exigido pelo pipeline (python para testes/script de e-mail, docker-cli para o build)
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip docker-cli docker-buildx \
    && docker --version \
    && docker buildx version \
    && rm -rf /var/lib/apt/lists/*

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Jenkins Configuration as Code: usuário, credenciais e job definidos por arquivo (sem GUI)
COPY casc.yaml /usr/share/jenkins/casc.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/casc.yaml

USER jenkins
