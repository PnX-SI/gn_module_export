library(httr2)

get_gn_export_data <- function(url, id_export, token, limit = 1000) {
    req <- build_request(url, id_export, token, limit)
    resps <- req_perform_iterative(
        req,
        next_req = iterate_with_offset(
            "offset",
            start = 0,
            offset = 1,
            resp_complete = is_complete
        ),
        max_reqs = Inf
    )

    all_data <- resps_data(
        resps, \(resp) resp_body_json(resp, simplifyVector = TRUE)$items
    )
    return(all_data)
}

is_complete <- function(resp) {
    length(resp_body_json(resp)$items) < resp_body_json(resp)$limit
}

build_request <- function(url, id_export, token, limit) {
    req <- request(url)
    req <- req |> req_url_path_append(id_export)
    params <- list(token = token, limit = limit)
    req <- req |> req_url_query(!!!params)
    return(req)
}
