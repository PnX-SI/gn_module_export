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
  . ~/geonature/external_modules/exports/config/settings.ini
  echo "Deactivating \"exports\" module"
  geonature deactivate_gn_module exports
  echo "Dropping \"gn_exports\" schema"
  psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -c "DROP SCHEMA IF EXISTS gn_exports CASCADE;"
  echo "Unregistering \"exports\" module "
  psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -c "DELETE FROM gn_commons.t_modules WHERE module_name='exports';"
  rm ~/geonature/external_modules/exports
  exit
fi

. config/settings.ini

touch config/conf_gn_module.toml
mkdir -p ~/geonature/backend/static/exports  # current_app.static_folder
echo -n "Create gn_exports schema"
PGPASSWORD=$user_pg_pass;psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -f data/exports.sql  &>> var/log/install_gn_module_exports.log
return_value=$?
check_psql_status $return_value

if [ "_$insert_sample_data" != "_" ]; then
    echo -n 'Populate exports with sample data'
    PGPASSWORD=$user_pg_pass;psql -h $db_host -p $db_port -U $user_pg -d $db_name -b -f data/sample.sql &>> var/log/install_gn_module_exports.log
    return_value=$?
    check_psql_status $return_value
fi
