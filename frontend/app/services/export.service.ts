import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpErrorResponse,
  HttpParams
} from "@angular/common/http";
import { BehaviorSubject } from "rxjs/BehaviorSubject";
import { ToastrService } from "ngx-toastr";

import { AppConfig } from "@geonature_config/app.config";

import { ModuleConfig } from "../module.config";

export interface Export {
  id: number;
  label: string;
  schema: string;
  view: string;
  desc: string;
  geometry_field: string;
  geometry_srid: number;
}

export interface ApiErrorResponse extends HttpErrorResponse {
  error: any | null;
  message: string;
  name: string;
}

@Injectable()
export class ExportService {

  constructor(private _api: HttpClient) {}

  getExports() {
    return this._api
      .get(`${AppConfig.API_ENDPOINT}/${ModuleConfig.MODULE_URL}/`);

  }

  downloadExport(x: Export, format: string, data:any) {
    return this._api
      .post(`${AppConfig.API_ENDPOINT}/${ModuleConfig.MODULE_URL}/${x.id}/${format}`,
      data)
  }

}
