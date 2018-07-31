#!/bin/bash
set -v
# Make sure only root can run our script
if [ "$(id -u)" == "0" ]; then
   echo "This script must not be run as root" 1>&2
   exit 1
fi

# FIXME: config path
. ~/geonature/config/settings.ini

mkdir -p /tmp/geonature

echo "Create exports schema..."
echo "--------------------" &> /var/log/geonature/install_exports_schema.log
echo "" &>> /var/log/geonature/install_exports_schema.log
cp data/exports.sql /tmp/geonature/exports.sql
sudo sed -i "s/MYLOCALSRID/$srid_local/g" /tmp/geonature/exports.sql
export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -f /tmp/geonature/exports.sql  &>> /var/log/geonature/install_exports_schema.log

echo "Cleaning files..."
    rm /tmp/geonature/*.sql
