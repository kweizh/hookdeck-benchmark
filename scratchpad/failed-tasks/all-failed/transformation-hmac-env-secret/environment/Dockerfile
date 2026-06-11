FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep gnupg && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/myproject && chmod 0755 /home/user/myproject

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck task environment: Hookdeck CLI + Node.js v24 + Python verifier toolchain for HMAC transformation tasks."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep gnupg
#   - always required pip3 packages: pytest-json-ctrf
#   - extra pip3 packages: requests (used by tests/test_final_state.py to call Hookdeck REST APIs)
#   - Node.js v24 (needed for hookdeck-cli)
#   - hookdeck-cli installed globally via npm (Hookdeck CLI for authentication and resource management)
#   - /home/user/myproject: empty working directory used by the task
