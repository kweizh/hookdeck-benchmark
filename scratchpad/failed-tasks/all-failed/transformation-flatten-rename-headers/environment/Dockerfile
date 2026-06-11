FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/hookdeck-task && chmod 0755 /home/user/hookdeck-task

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck task environment with the hookdeck CLI and Node.js v24 for building a Connection with a JavaScript Transformation rule."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - additional apt packages: jq (for inspecting JSON responses from the Hookdeck API)
#   - Node.js v24 (required by the hookdeck-cli npm package)
#   - hookdeck-cli installed globally via npm (https://hookdeck.com)
#   - pip3 packages: pytest-json-ctrf (required), requests (used by test_final_state.py)
#   - /home/user/hookdeck-task: working directory for the task
