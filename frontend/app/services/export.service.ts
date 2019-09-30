import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpErrorResponse
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
  exports: BehaviorSubject<Export[]>;
  downloadProgress: BehaviorSubject<number>;

  constructor(private _api: HttpClient, private toastr: ToastrService) {
    this.exports = <BehaviorSubject<Export[]>>new BehaviorSubject([]);
    this.downloadProgress = <BehaviorSubject<number>>new BehaviorSubject(0.0);
  }

  getExports() {
    this._api
      .get(`${AppConfig.API_ENDPOINT}/${ModuleConfig.MODULE_URL}/`)
      .subscribe(
        (exports: Export[]) => this.exports.next(exports),
        (response: ApiErrorResponse) => {
          this.toastr.error(
            response.error.message ? response.error.message : response.message,
            response.error.api_error ? response.error.api_error : response.name,
            { timeOut: 0 }
          );
          console.error("api error:", response);
        },
        () => {
          console.info(`export service: ${this.exports.value.length} exports`);
          console.debug("exports:", this.exports.value);
        }
      );
  }

  downloadExport(x: Export, format: string) {
    this._api.get(`${AppConfig.API_ENDPOINT}/${ModuleConfig.MODULE_URL}/${x.id}/${format}`)
    .subscribe(
      response => {
        this.toastr.success(
          response && response.message ? response.message : ''
        )
      },
      (response: ApiErrorResponse) => {
        this.toastr.error(
          response.error.message ? response.error.message : response.message,
          response.error.api_error ? response.error.api_error : response.name,
          { timeOut: 0 }
        );
      }
    )
  }

}
