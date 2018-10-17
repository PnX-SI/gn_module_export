#!/bin/bash

mkdir -p var/log

check_psql_status() {
  if [ $1 -eq 0 ]; then
    echo -e ' \e[92mOK\e[0m'
  else
    echo -n -e ' \e[91mnot OK\e[0m'
    if [ $1 -eq 1 ]; then
      echo ': fatal error.'
    elif [ $1 -eq 2 ]; then
      echo ": connection with server ${db_host}:${db_port} on db ${db_name} was terminated abnormally."
    elif [ $1 -eq 3 ]; then
      echo ": an error occurred in the script."
    fi
    exit $1
  fi
}

if [ $(basename "$0") = 'uninstall.sh' ]; then
  set -x
  . ~/geonature/external_modules/exports/config/settings.ini
  set +x
  geonature deactivate_gn_module exports
  psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -c "DROP SCHEMA IF EXISTS gn_exports CASCADE; DELETE FROM gn_commons.t_modules WHERE module_name='exports';"
  rm ~/geonature/external_modules/exports
  exit
fi

set -x
. config/settings.ini
set +x

touch config/conf_gn_module.toml

echo -n "Create gn_exports schema"
PGPASSWORD=$user_pg_pass;psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -c 'DROP SCHEMA IF EXISTS gn_exports CASCADE; CREATE SCHEMA gn_exports;' &>> var/log/install_gn_module_exports.log
return_value=$?
check_psql_status $return_value

echo -n "Create tables"
# sed -i "s/MY_LOCAL_SRID/$srid_local/g" /tmp/geonature/exports.sql
PGPASSWORD=$user_pg_pass;psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -f data/exports.sql  &>> var/log/install_gn_module_exports.log
return_value=$?
check_psql_status $return_value

if [ $insert_sample_data = true ]; then
    echo -n 'Populating exports with sample data'
    PGPASSWORD=$user_pg_pass;psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -f data/sample.sql &>> var/log/install_gn_module_exports.log
    return_value=$?
    check_psql_status $return_value
fi
