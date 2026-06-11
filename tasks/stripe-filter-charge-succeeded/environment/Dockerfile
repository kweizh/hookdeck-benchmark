FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm i -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/hookdeck-task && chmod 0755 /home/user/hookdeck-task

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck CLI environment for Stripe charge.succeeded filter task with Mock API destination."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq
#   - always required pip3 packages: pytest-json-ctrf
#   - requests (Python) for REST-based verification of Hookdeck resources and events
#   - Node.js v24 + hookdeck-cli (npm global) so `hookdeck` is available on PATH
#   - /home/user/hookdeck-task: working directory for the task
