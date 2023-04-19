FROM  python:3.10-bullseye

# Authorize SSH Host
# RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN mkdir -p ~/.ssh && \
    chmod 0700 ~/.ssh && \
    ssh-keyscan github.com > ~/.ssh/known_hosts

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN --mount=type=ssh  pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "./check_status.py" ]
