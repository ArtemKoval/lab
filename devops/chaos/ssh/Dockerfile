FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server iptables \
    && rm -rf /var/lib/apt/lists/*

# The '*' hash unlocks both accounts for pubkey auth and keeps
# password logins dead. The locked field of useradd makes sshd
# deny every auth method, and that hides every injected fault.
RUN useradd -m -s /bin/bash practice \
    && useradd -m -s /bin/bash guest \
    && usermod -p '*' practice \
    && usermod -p '*' guest \
    && mkdir -p /run/sshd /opt/chaos/inject /etc/chaos/sshd_extra.d \
    && mkdir -p /home/practice/.ssh \
    && touch /home/practice/.ssh/authorized_keys \
    && chown -R practice:practice /home/practice/.ssh

COPY environments/chaos-start.sh /usr/local/bin/chaos-start.sh
COPY environments/inject/ /opt/chaos/inject/
RUN chmod +x /usr/local/bin/chaos-start.sh /opt/chaos/inject/*.sh /opt/chaos/inject/_setup/*.sh

CMD ["sleep", "infinity"]
