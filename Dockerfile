FROM ubuntu:18.04

ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Installing Python 3.8 and tools
RUN apt-get update \
    && apt-get install -y \
        python3.8 \
        python3.8-dev \
        python3.8-venv \
        python3-pip

# Installing bash tools
RUN apt-get -qy --no-install-recommends install \
        sudo \
        unzip \
        wget \
        curl \
        libxi6 \
        libgconf-2-4 \
        vim \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update \
    && apt-get install -y postgresql-server-dev-10

# Installing Chrome
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && printf "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get -yqq update \
    && apt-get -yqq install google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Configuring Chrome
RUN dpkg-divert --add --rename --divert /opt/google/chrome/google-chrome.real /opt/google/chrome/google-chrome \
    && printf "#!/bin/bash\nexec /opt/google/chrome/google-chrome.real \"\$@\"" > /opt/google/chrome/google-chrome \
    && chmod 755 /opt/google/chrome/google-chrome

# Creating project directory
RUN mkdir -p {/code/post_parser,/code/tests}

# Copying project files
COPY requirements.txt /code/

RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add - \
    && sudo apt-get update \
    && apt-get install -y postgresql-12

RUN sudo apt-get install -y build-essential libssl-dev libffi-dev
# Intalling requirements
RUN cd code \
    && python3.8 -m venv venv \
    && bash -c "sudo -s && source /code/venv/bin/activate && python -m pip install -r /code/requirements.txt"

# Configuring virtual display
RUN set -e
RUN Xvfb -ac :99 -screen 0 1920x1080x16 > /dev/null 2>&1 &
RUN export DISPLAY=:99
RUN exec "$@"

# Installing Chrome Driver
ENV CHROMEDRIVER_DIR /chromedriver
ENV PATH $CHROMEDRIVER_DIR:$PATH
RUN mkdir $CHROMEDRIVER_DIR \
    && wget -q --continue -P $CHROMEDRIVER_DIR "https://chromedriver.storage.googleapis.com/88.0.4324.96/chromedriver_linux64.zip" \
    && unzip $CHROMEDRIVER_DIR/chromedriver* -d $CHROMEDRIVER_DIR

COPY run.py server.py .env /code/
COPY post_parser /code/post_parser
COPY tests /code/tests

CMD ["/bin/bash"]
