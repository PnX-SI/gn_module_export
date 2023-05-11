import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ConfigService } from '@geonature/services/config.service';

export type JsonData = { [key: string]: any };

export interface Export {
  id: number;
  label: string;
  schema: string;
  view: string;
  desc: string;
  geometry_field: string;
  geometry_srid: number;
  cor_roles_exports: JsonData[];
}

export interface ApiErrorResponse extends HttpErrorResponse {
  error: any | null;
  message: string;
}

@Injectable()
export class ExportService {
  constructor(private _api: HttpClient, public config: ConfigService) {}

  getExports() {
    console.log(this.config.API_ENDPOINT, this.config.EXPORTS.MODULE_URL);
    return this._api.get(`${this.config.API_ENDPOINT}${this.config.EXPORTS.MODULE_URL}/`);
  }

  downloadExport(x: Export, format: string, data: any) {
    return this._api.post<any>(
      `${this.config.API_ENDPOINT}${this.config.EXPORTS.MODULE_URL}/${x.id}/${format}`,
      data
    );
  }
}
