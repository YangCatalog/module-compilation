FROM python:3.9-bullseye
ARG YANG_ID
ARG YANG_GID
ARG CRON_MAIL_TO
ARG YANGCATALOG_CONFIG_PATH
ARG CONFD_VERSION
ARG YANGLINT_VERSION
ARG XYM_VERSION

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"
ENV CRON_MAIL_TO "$CRON_MAIL_TO"
ENV YANGCATALOG_CONFIG_PATH "$YANGCATALOG_CONFIG_PATH"
ENV CONFD_VERSION "$CONFD_VERSION"
ENV YANGLINT_VERSION "$YANGLINT_VERSION"
ENV XYM_VERSION "$XYM_VERSION"
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN echo "export PATH=$VIRTUAL_ENV/bin:$PATH" >/etc/environment
ENV GIT_PYTHON_GIT_EXECUTABLE=/usr/bin/git

ENV YANG=/.
ENV YANGVAR="get_config.py --section Directory-Section --key var"
ENV BIN=$YANG/module-compilation/bin
ENV CONF=$YANG/module-compilation/conf
ENV BACKUPDIR="get_config.py --section Directory-Section --key backup"
ENV CONFD_DIR="get_config.py --section Tool-Section --key confd-dir"
ENV PYANG="get_config.py --section Tool-Section --key pyang-exec"
ENV PYANG_PLUGINPATH="/module-compilation/bin/utility/pyang_plugin"
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

ENV VIRTUAL_ENV=/module-compilation

RUN groupadd -g ${YANG_GID} -r yang && useradd --no-log-init -r -g yang -u ${YANG_ID} -d $VIRTUAL_ENV yang

WORKDIR $VIRTUAL_ENV

RUN echo postfix postfix/mailname string yangcatalog.org | debconf-set-selections
RUN echo postfix postfix/main_mailer_type string 'Internet Site' | debconf-set-selections

RUN apt-get -y update
RUN apt-get -y install build-essential clang cmake cron gnupg2 libpcre2-dev libssl1.1 \
  libssl-dev libxml2-dev postfix python2.7 python3-pip rsync rsyslog systemd pypy3 \
  zlib1g-dev libncurses5-dev zstd

WORKDIR /home
RUN git clone -b ${YANGLINT_VERSION} --single-branch --depth 1 https://github.com/CESNET/libyang.git
RUN git clone https://github.com/decalage2/pyhtgen.git
RUN mv /home/pyhtgen/setup.py /home/pyhtgen/pyhtgen
RUN python2.7 /home/pyhtgen/pyhtgen/setup.py install
RUN mkdir -p /home/libyang/build
WORKDIR /home/libyang/build
RUN cmake -D CMAKE_BUILD_TYPE:String="Release" .. && make && make install

WORKDIR $VIRTUAL_ENV
RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
COPY ./module-compilation/requirements.txt .
RUN pip3 install -r requirements.txt
RUN pip3 install xym==${XYM_VERSION} -U
RUN pypy3 -mpip install pyang==2.5.3

RUN mkdir /opt/confd
COPY ./resources/* $VIRTUAL_ENV/
COPY ./resources/main.cf /etc/postfix/main.cf
COPY ./conf/yangdump-pro.conf /etc/yumapro/yangdump-pro.conf
COPY ./conf/yangdump-pro-allinclusive.conf /etc/yumapro/yangdump-pro-allinclusive.conf
RUN ./confd-${CONFD_VERSION}.linux.x86_64.installer.bin /opt/confd

# This is a workaround for correct extraction of yumapro 21.10 release.
RUN ./repack.sh yumapro-client-21.10-12.u2204.amd64.deb
RUN dpkg -i package.deb

# Setup cron job
COPY ./module-compilation/crontab /etc/cron.d/ietf-cron
RUN chown yang:yang /etc/cron.d/ietf-cron
RUN chmod 0644 /etc/cron.d/ietf-cron
RUN sed -i "s|<MAIL_TO>|${CRON_MAIL_TO}|g" /etc/cron.d/ietf-cron
RUN sed -i "s|<YANGCATALOG_CONFIG_PATH>|${YANGCATALOG_CONFIG_PATH}|g" /etc/cron.d/ietf-cron
RUN sed -i "/imklog/s/^/#/" /etc/rsyslog.conf

RUN rm -rf /usr/bin/python
RUN ln -s /usr/bin/python3 /usr/bin/python
COPY ./module-compilation $VIRTUAL_ENV
RUN cd /module-compilation/bin/resources/HTML && python setup.py install

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
CMD cron && service postfix start && service rsyslog start && touch /var/yang/logs/cronjob-daily.log && tail -f /var/yang/logs/cronjob-daily.log
