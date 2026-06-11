FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/hookdeck-fanout && chmod 0755 /home/user/hookdeck-fanout

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck fan-out evaluation environment: hookdeck CLI, curl, and Python (requests) for driving the REST + Publish APIs against Mock API destinations with per-destination rate limits."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (used to install hookdeck-cli globally via npm)
#   - hookdeck CLI for managing sources, destinations, and connections
#   - python3 `requests` library for orchestration helpers and the final-state verifier
#   - /home/user/hookdeck-fanout: working directory the executor uses for the task and its output.log
