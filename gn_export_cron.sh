#!/bin/sh
# set -x

USERNAME=
PASSWORD=
X_ID=
X_FORMAT=
X_FILE=
TOKEN=

while :; do
    case $1 in
        -h|-\?|--help)
            echo "Performs a GéoNature export from hosted instance."
            echo "$(basename $0) -u username -p password -id int -f csv -o some_path_to_output_file"
            exit
            ;;

        -u|--user)
            if [ -n "$2" ]; then
                USERNAME=$2
                shift
            else
                printf 'ERROR: "--user" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --user=?*)
            USERNAME=${1#*=}
            ;;

        -p|--password)
            if [ -n "$2" ]; then
                PASSWORD=$2
                shift
            else
                printf 'ERROR: "--password" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --password=?*)
            PASSWORD=${1#*=}
            ;;

        -id|--id)
            if [ -n "$2" ]; then
                X_ID=$2
                shift
            else
                printf 'ERROR: "--id" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --id=?*)
            X_ID=${1#*=}
            ;;

        -f|--format)
            if [ -n "$2" ]; then
                X_FORMAT=$2
                shift
            else
                printf 'ERROR: "--format" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --format=?*)
            X_FORMAT=${1#*=}
            ;;

        -o|--output)
            if [ -n "$2" ]; then
                X_FILE=$2
                shift
            else
                printf 'ERROR: "--output" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --output=?*)
            X_FILE=${1#*=}
            ;;

        -t|--token)
            if [ -n "$2" ]; then
                TOKEN=$2
                shift
            else
                printf 'ERROR: "--token" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --token=?*)
            TOKEN=${1#*=}
            ;;

        --)
            shift
            break
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            ;;
        *)
            break
    esac

    shift
done

check_request_status() {
    if [ "$1" != "0" ]; then
       echo "Fetching operation for export $X_ID failed with status $1"
       exit $1
    fi
}

fetch_export() {
    curl -s -H 'Accept: application/json' -H 'Content-Type: application/json' --cookie "token=${TOKEN}" \
        --create-dirs --remote-time -o "$X_FILE" \
        --url ${API_ENDPOINT}${API_URL}/${X_ID}/${X_FORMAT}
    status=$?
    check_request_status $status
}

login() {
    _response=$(\
        curl -s -i -k --cookie-jar - \
            -X POST -H 'Accept: application/json' -H 'Content-Type: application/json' \
            --data "{\"login\":\"${USERNAME}\",\"password\":\"${PASSWORD}\", \"id_application\":\"${ID_APPLICATION}\",\"with_cruved\": \"true\"}" \
            ${API_ENDPOINT}/auth/login )
    status=$?
    check_request_status $status

    TOKEN=$(echo ${_response} | grep -oE 'Set-Cookie: token=([^;]*);' | sed -E 's/^Set-Cookie: token=([^;]*);/\1/')
    [ "_${TOKEN}" = "_" ] && echo 'ERROR: Failed to obtain api token for endpoint $ENDPOINT.' && exit 127
}

USERNAME=${USERNAME:-'admin'}
PASSWORD=${PASSWORD:-'admin'}
X_ID=${X_ID:-2}
X_FORMAT=${X_FORMAT:-'json'}
X_FILE="${X_FILE:-${HOME}/geonature/backend/static/exports/export_sinp.json}"

ID_APPLICATION=$(grep ID_APPLICATION_GEONATURE ~/geonature/config/geonature_config.toml | cut -f3 -d ' ')
API_ENDPOINT=$(grep API_ENDPOINT ~/geonature/config/geonature_config.toml | cut -f3 -d ' ' | sed -e "s/'//g")
API_URL=$(grep api_url ~/geonature/external_modules/exports/config/conf_gn_module.toml | cut -f3 -d ' ' | sed -e "s/'//g")

if [ "_${TOKEN}" = "_" ]; then
    login
fi

fetch_export

# cd ~/
# curl -# --get -H 'Accept: application/json' -H 'Content-Type: application/json' --cookie "token=${TOKEN}" \
#     --remote-time --remote-name --remote-header-name \
#     --url ${API_ENDPOINT}${API_URL}/etalab_export
