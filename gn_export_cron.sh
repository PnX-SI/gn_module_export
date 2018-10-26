#!/bin/sh

USRNAME=
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
                USRNAME=$2
                shift
            else
                printf 'ERROR: "--user" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;

        --user=?*)
            USRNAME=${1#*=}
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
    case "$2" in
        0|20*)
            # >&2 echo "\e[92m${1} operation for export $X_ID succeeded with status ${2}\e[0m"
            ;;
        *)
            >&2 echo "\e[91m${1} operation for export $X_ID failed with status ${2}.\e[0m"
            [ "_$3" != "" ] && >&2 echo "${3}"
            exit $1
            ;;
    esac
}

fetch_export() {
    curl -s --cookie "token=${TOKEN}" \
        -H 'Accept: application/json' -H 'Content-Type: application/json' \
        --create-dirs --remote-time -o "$X_FILE" \
        --url ${API_ENDPOINT}${API_URL}/${X_ID}/${X_FORMAT}
    status=$?
    check_request_status 'fetch' $status
}

login() {
    # set -x
    _response=$(\
        curl --silent --include \
            -X POST -H 'Accept: application/json' -H 'Content-Type: application/json' \
            --data "{\"login\":\"${USRNAME}\",\"password\":\"${PASSWORD}\", \"id_application\":\"${ID_APPLICATION}\",\"with_cruved\": \"true\"}" \
            ${API_ENDPOINT}/auth/login )
    # set +x
    status=$?
    check_request_status 'login' $status "$_response"
    echo "$_response"
}

extract_token() {
    TOKEN=$(echo "${1}" | grep -E '^Set-Cookie: token=([^;]*);.*' | sed -E 's/^Set-Cookie: token=([^;]*);.*/\1/')
    # >&2 echo "->token: <${TOKEN}>"
    [ "_${TOKEN}" = "_" ] && \
        >&2 echo "ERROR: Failed to obtain api token for endpoint ${API_ENDPOINT}." && exit 127
}

# TODO: source env conf
USRNAME=${USRNAME:-'admin'}
PASSWORD=${PASSWORD:-'admin'}
X_ID=${X_ID:-2}
X_FORMAT=${X_FORMAT:-'json'}
X_FILE="${X_FILE:-${HOME}/geonature/backend/static/exports/export_sinp.json}"

ID_APPLICATION=$(grep ID_APPLICATION_GEONATURE ~/geonature/config/geonature_config.toml | cut -f3 -d ' ')
API_ENDPOINT=$(grep API_ENDPOINT ~/geonature/config/geonature_config.toml | cut -f3 -d ' ' | sed -e "s/'//g")
API_URL=$(grep api_url ~/geonature/external_modules/exports/config/conf_gn_module.toml | cut -f3 -d ' ' | sed -e "s/'//g")

if [ "_${TOKEN}" = "_" ]; then
    cookie=$(login)
    extract_token "$cookie"
fi

if [ "_${TOKEN}" != "_" ]; then
  fetch_export
fi

# cd ~/
# &2 echo "Fetching ${API_ENDPOINT}${API_URL}/${X_ID}/${X_FORMAT}"
# curl -# --get --cookie "token=${TOKEN}" \
#     -H 'Accept: application/json' -H 'Content-Type: application/json' \
#     --remote-time --remote-name --remote-header-name \
#     --url "${API_ENDPOINT}${API_URL}/${X_ID}/${X_FORMAT}"
