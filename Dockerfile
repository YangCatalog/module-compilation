FROM ubuntu:18.04
ARG YANG_ID
ARG YANG_GID
ARG CRON_MAIL_TO

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"
ENV CRON_MAIL_TO "$CRON_MAIL_TO"
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN echo "export PATH=$VIRTUAL_ENV/bin:$PATH" > /etc/environment
ENV GIT_PYTHON_GIT_EXECUTABLE=/usr/bin/git

ENV YANG=/.
ENV YANGVAR="get_config.py --section Directory-Section --key var"
ENV BIN=$YANG/sdo_analysis/bin
ENV CONF=$YANG/sdo_analysis/conf
ENV BACKUPDIR="get_config.py --section Directory-Section --key backup"
ENV CONFD_DIR="get_config.py --section Tool-Section --key confd-dir"
ENV PYANG="get_config.py --section Tool-Section --key pyang-exec"
ENV IS_PROD="get_config.py --section General-Section --key is-prod"

#
# Repositories
#
ENV NONIETFDIR="get_config.py --section Directory-Section --key non-ietf-directory"
ENV IETFDIR="get_config.py --section Directory-Section --key ietf-directory"
ENV MODULES="get_config.py --section Directory-Section --key modules-directory"

#
# Working directories
#
ENV LOGS="get_config.py --section Directory-Section --key logs"
ENV TMP="get_config.py --section Directory-Section --key temp"

#
# Where the HTML pages lie
#
ENV WEB_PRIVATE="get_config.py --section Web-Section --key private-directory"
ENV WEB_DOWNLOADABLES="get_config.py --section Web-Section --key downloadables-directory"
ENV WEB="get_config.py --section Web-Section --key public-directory"

ENV VIRTUAL_ENV=/sdo_analysis

RUN groupadd -g ${YANG_GID} -r yang \
  && useradd --no-log-init -r -g yang -u ${YANG_ID} -d $VIRTUAL_ENV yang

WORKDIR $VIRTUAL_ENV

ENV confd_version 7.5

RUN echo postfix postfix/mailname string yangcatalog.org | debconf-set-selections; \
  echo postfix postfix/main_mailer_type string 'Internet Site' | debconf-set-selections

RUN apt-get -y update
RUN apt-get -y install build-essential clang cmake cron curl git gnupg2 libpcre2-dev libssl1.0.0 \
  libssl-dev libxml2-dev openssh-client postfix python3.6 python3-pip rsync rsyslog systemd wget \
  && cd /home; mkdir w3cgrep \
  && cd /home; git clone https://github.com/CESNET/libyang.git \
  && cd /home/libyang; mkdir build \
  && cd /home/libyang/build && cmake .. && make && make install

RUN cd /home; git clone https://github.com/decalage2/pyhtgen.git \
  && mv /home/pyhtgen/setup.py /home/pyhtgen/pyhtgen; cd /home/pyhtgen/pyhtgen;  python setup.py install

RUN rm  -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
COPY ./sdo_analysis/requirements.txt .
RUN pip3 install -r requirements.txt

RUN mkdir /opt/confd
COPY ./resources/* $VIRTUAL_ENV/
COPY ./resources/main.cf /etc/postfix/main.cf
COPY ./conf/yangdump-pro.conf /etc/yumapro/yangdump-pro.conf
COPY ./conf/yangdump-pro-allinclusive.conf /etc/yumapro/yangdump-pro-allinclusive.conf
RUN ./confd-${confd_version}.linux.x86_64.installer.bin /opt/confd
RUN dpkg -i yumapro-client-20.10-9.u1804.amd64.deb

# Setup cron job
COPY ./sdo_analysis/crontab /etc/cron.d/ietf-cron
RUN chown yang:yang /etc/cron.d/ietf-cron
RUN chmod 0644 /etc/cron.d/ietf-cron
RUN sed -i "s|<MAIL_TO>|${CRON_MAIL_TO}|g" /etc/cron.d/ietf-cron

RUN rm -rf /usr/bin/python
RUN ln -s /usr/bin/python3 /usr/bin/python
COPY ./sdo_analysis $VIRTUAL_ENV
RUN cd /sdo_analysis/bin/resources/HTML; python setup.py install

RUN chmod 0777 bin/configure.sh

RUN chown -R yang:yang $VIRTUAL_ENV
USER ${YANG_ID}:${YANG_GID}
RUN crontab /etc/cron.d/ietf-cron

WORKDIR /

RUN git config --global user.name miroslavKovacPantheon
RUN git config --global user.email miroslav.kovac@panetheon.tech

WORKDIR $VIRTUAL_ENV

USER root:root
# Run the command on container startup
CMD cron && service postfix start && service rsyslog start && tail -f /var/yang/logs/cronjob-daily.log
