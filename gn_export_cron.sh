#!/bin/sh


check_request_status() {
    case "$1" in
        0|20*)
            # OK
            ;;
        *)
            >&2 echo "\e[91mFetch command failed with status ${1}.\e[0m"
            [ "_$2" != "" ] && >&2 echo "${2}"
            exit $1
            ;;
    esac
}

fetch_export() {
    curl -s \
        -H 'Accept: application/json' -H 'Content-Type: application/json' \
        --create-dirs --remote-time -o "$X_FILE" \
        --url ${API_ENDPOINT}${API_URL}/etalab
    status=$?
    check_request_status $status
}

X_FILE="${X_FILE:-${HOME}/geonature/backend/static/exports/export_etalab.ttl}"

# TODO: request http://instance_name/gn_commons/modules and get module_path but no ID_APPLICATION
#       alternative:
ID_APPLICATION=1  # FIXME: $(grep ID_APPLICATION ~/geonature/config/geonature_config.toml | cut -f3 -d ' ')
API_ENDPOINT=$(grep API_ENDPOINT ~/geonature/config/geonature_config.toml | cut -f3 -d ' ' | sed -e "s/'//g")
API_URL=$(grep api_url ~/geonature/external_modules/exports/config/conf_gn_module.toml | cut -f3 -d ' ' | sed -e "s/'//g")

fetch_export
