#!/bin/bash
. config/settings.ini

# Create log folder in module folders if it don't already exists
if [ ! -d 'var' ]
then
  mkdir var
fi

if [ ! -d 'var/log' ]
then
  mkdir var/log
fi

mkdir -p /tmp/geonature

echo "Create exports schema..."
cp data/exports.sql /tmp/geonature/exports.sql
# sudo sed -i "s/MY_LOCAL_SRID/$srid_local/g" /tmp/geonature/exports.sql
export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -f /tmp/geonature/exports.sql  &>> var/log/install_gn_module_exports.log

echo "Cleaning files..."
    rm /tmp/geonature/*.sql
