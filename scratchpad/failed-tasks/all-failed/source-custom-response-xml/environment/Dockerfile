FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep jq && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nodejs && \
    npm install -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/hookdeck-task && chmod 0755 /home/user/hookdeck-task

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck task environment with Node.js v24 and Hookdeck CLI installed for provisioning sources, destinations, and connections via CLI or REST API."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - extra apt packages: jq (for shell-based JSON parsing if the executor chooses curl)
#   - always required pip3 packages: pytest-json-ctrf
#   - extra pip3 packages: requests (used by tests/test_final_state.py for Hookdeck REST API verification)
#   - Node.js v24 from NodeSource (required by hookdeck-cli npm install)
#   - hookdeck-cli installed globally via npm so the `hookdeck` binary is on PATH
#   - /home/user: home directory
#   - /home/user/hookdeck-task: empty project directory where the executor writes output.log
