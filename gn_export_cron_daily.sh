#!/bin/bash

connection="postgresql://geonatuser:monpassachanger@localhost:5432/geonaturedb"
psql $connection -c 'SELECT exports_logs_delete_function()'
