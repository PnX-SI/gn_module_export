#!/bin/bash
# FIXME: source GN config and interpolate vars in cron job template

BINDIR=${HOME}/.local/bin
CRONJOB='gn_export_cron_daily.sh'
MAX_DELAY=10

mkdir -p ${BINDIR}
cp -v ${CRONJOB} "${BINDIR}/${CRONJOB}"
chmod 544 "${BINDIR}/${CRONJOB}"

buffer=$(mktemp)
crontab -l > ${buffer}
echo "00 $(($RANDOM%MAX_DELAY)) * * * ${HOME}/.local/bin/gn_export_cron_daily.sh" >> ${buffer}
crontab ${buffer}
rm ${buffer}
