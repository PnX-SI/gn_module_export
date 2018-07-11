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
  id: string;
  label: string;
  selection: string;
  extension: string;
  start: Date;
}

export interface ExportLabel {
  label: string;
  start: Date;
}

const apiEndpoint='http://localhost:8000/exports';


export const FormatMapMime = new Map([
  ['csv', 'text/csv'],
  ['json', 'application/json'],
  ['rdf', 'application/rdf+xml']
])

@Injectable()
export class ExportService {
  exports: BehaviorSubject<Export[]>
  labels: BehaviorSubject<ExportLabel[]>
  downloadProgress: BehaviorSubject<number>
  private _blob: Blob

  constructor(private _api: HttpClient) {
    this.exports = <BehaviorSubject<Export[]>>new BehaviorSubject([]);
    this.labels = <BehaviorSubject<ExportLabel[]>>new BehaviorSubject([]);
    this.downloadProgress = <BehaviorSubject<number>>new BehaviorSubject(0.0);
  }

  // QUESTION: loader ?
  getExports() {
    this._api.get(`${apiEndpoint}/all`).subscribe(
      (exports: Export[]) => this.exports.next(exports),
      error => console.error(error),
      () => {
        console.info(`export service: ${this.exports.value.length} exports`)
        console.debug('exports:',  this.exports.value)
        this.getLabels()
      }
    )
  }

  getLabels() {

    function byLabel (a, b) {
      const labelA = a.label.toUpperCase()
      const labelB = b.label.toUpperCase()
      return (labelA < labelB) ? -1 : (labelA > labelB) ? 1 : 0
    }

    let labels = []
    this.exports.subscribe(xs => xs.map((x) => labels.push({label: x.label, start: x.start})))
    let seen = new Set()
    let uniqueLabels = labels.filter((item: ExportLabel) => {
                                let k = item.label
                                return seen.has(k) ? false : seen.add(k)
                              })
    this.labels.next(uniqueLabels.sort(byLabel))
  }

  downloadExport(ts: number, label: string, extension: string) {

    const downloadExportURL = `${apiEndpoint}/download/export_${label}_${ts}.${extension}`

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
            const kb = (parseFloat(event.loaded) / 1024).toFixed(2);
             this.downloadProgress.next(kb)
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
      let date = new Date(0)
      date.setUTCSeconds(ts)
      this.saveBlob(this._blob, `export_${label}_${date.toISOString()}.${extension}`)
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
