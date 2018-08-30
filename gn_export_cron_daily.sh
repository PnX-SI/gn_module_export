#!/bin/bash
connection="postgresql://geonatuser:monpassachanger@localhost:5432/geonaturedb"
psql $connection -c 'SELECT gn_exports.logs_delete_function()'
