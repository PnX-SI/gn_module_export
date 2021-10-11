#!/bin/bash

geonature_dir=$1

cd $geonature_dir
source backend/venv/bin/activate
geonature exports gn_exports_run_cron_export
deactivate