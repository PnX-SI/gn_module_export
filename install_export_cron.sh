#!/bin/sh
# set -x

JOB_PATH="${HOME}/geonature/external_modules/exports/gn_export_cron.sh"
MAX_DELAY=10

if [ -n "$RANDOM" ]; then
    n=$RANDOM
elif [ -c /dev/urandom ]; then
    n=$(\
        (echo ibase=16; dd if=/dev/urandom bs=1 count=4 2>/dev/null |
        od -tx1 |
        sed -n '$q;p' |
        cut -d ' ' -f2- |
        tr -d ' ' | tr -d '\134\012'|
        cut -c1-2 |
        tr '[a-f]' '[A-F]') |
        bc | tr -d '\134\012')
fi

chmod 544 "${JOB_PATH}"

buffer=$(mktemp)
crontab -l > ${buffer}
echo "00 $((${n} % MAX_DELAY)) * * * $JOB_PATH" >> ${buffer}
crontab ${buffer}
rm ${buffer}
