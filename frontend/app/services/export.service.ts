import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpEvent,
  HttpHeaders,
  HttpRequest,
  HttpEventType,
  HttpErrorResponse
} from "@angular/common/http";
import { Observable } from "rxjs/Observable";
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { filter } from "rxjs/operator/filter";
import { map } from "rxjs/operator/map";

import { AppConfig } from "@geonature_config/app.config";


export interface Export {
  id: number;
  id_creator: number;
  label: string;
  schema: string;
  view: string;
  desc: string;
  created: Date;
  updated: Date;
  deleted: Date;
}

const apiEndpoint='http://localhost/geonature/api/exports';

export const FormatMapMime = new Map([
  ['csv', 'text/csv'],
  ['json', 'application/json'],
  ['rdf', 'application/rdf+xml']
])

@Injectable()
export class ExportService {
  exports: BehaviorSubject<Export[]>
  downloadProgress: BehaviorSubject<number>
  private _blob: Blob

  constructor(private _api: HttpClient) {
    this.exports = <BehaviorSubject<Export[]>>new BehaviorSubject([]);
    this.downloadProgress = <BehaviorSubject<number>>new BehaviorSubject(0.0);
  }

  getExports() {
    this._api.get(`${apiEndpoint}/`).subscribe(
      (exports: Export[]) => this.exports.next(exports),
      error => console.error(error),
      () => {
        console.info(`export service: ${this.exports.value.length} exports`)
        console.debug('exports:',  this.exports.value)
      }
    )
  }

  getLabels() {
    let labels = []
    let subscription = this.exports.subscribe(
      xs => xs.map((x) => labels.push({
        label: x.label,
        date: x.updated ? x.updated : x.created,
        description: x.desc,
        creator: x.id_creator
      })),
      error => console.error(error),
      () => subscription.unsubscribe())
    return labels
  }

  downloadExport(xport: Export, extension: string) {
    let downloadExportURL = `${apiEndpoint}/export/${xport.id}/${extension}`

    let source = this._api.get(downloadExportURL, {
      headers: new HttpHeaders().set('Content-Type', `${FormatMapMime.get(extension)}`),
      observe: 'events',
      responseType: 'blob',
      reportProgress: true,
    })
    let subscription = source.subscribe(
      event => {
        if (event.type === HttpEventType.DownloadProgress) {
          if (event.hasOwnProperty('total')) {
            const percentage = Math.round((100 / event.total) * event.loaded);
            this.downloadProgress.next(percentage)
          } else {
            const kb = (event.loaded / 1024).toFixed(2);
             this.downloadProgress.next(parseFloat(kb))
          }
      }
      if (event.type === HttpEventType.Response) {
        this._blob = new Blob([event.body], {type: event.headers.get('Content-Type')});
      }
    },
    (e: HttpErrorResponse) => {
      console.error(e.error);
      console.error(e.name);
      console.error(e.message);
      console.error(e.status);
    },
    () => {
      let date = new Date(xport.updated ? xport.updated : xport.created)
      this.saveBlob(this._blob, `export_${xport.label}_${date.toISOString()}.${extension}`)
      subscription.unsubscribe()
    }
  )}

  saveBlob(blob, filename) {
    let link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.setAttribute('visibility','hidden')
    link.download = filename
    link.onload = function() { URL.revokeObjectURL(link.href) }
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}
