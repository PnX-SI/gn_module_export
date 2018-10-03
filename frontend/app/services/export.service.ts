import { Injectable } from '@angular/core'
import {
  HttpClient,
  HttpEvent,
  HttpHeaders,
  HttpRequest,
  HttpEventType,
  HttpErrorResponse
} from '@angular/common/http'
import { Observable } from 'rxjs/Observable'
import { BehaviorSubject } from 'rxjs/BehaviorSubject'
import { filter } from 'rxjs/operator/filter'
import { map } from 'rxjs/operator/map'
import { ToastrService } from 'ngx-toastr'

import { Constants } from '../const'

export interface Export {
  id: number
  label: string
  schema: string
  view: string
  desc: string
  geometry_field: string
  geometry_srid: number
}

export interface Collection {
  name: string
  tables: any[]
}

export interface ApiErrorResponse extends HttpErrorResponse {
  error: any | null
  message: string
  name: string
}


export const FormatMapMime = new Map([
  ['csv', 'text/csv'],
  ['json', 'application/json'],
  ['shp', 'application/zip'],
  ['rdf', 'application/rdf+xml']
])

@Injectable()
export class ExportService {
  exports: BehaviorSubject<Export[]>
  collections: BehaviorSubject<Collection[]>
  downloadProgress: BehaviorSubject<number>
  private _blob: Blob

  constructor(private _api: HttpClient, private toastr: ToastrService) {
    this.exports = <BehaviorSubject<Export[]>>new BehaviorSubject([])
    this.collections = <BehaviorSubject<Collection[]>>new BehaviorSubject([])
    this.downloadProgress = <BehaviorSubject<number>>new BehaviorSubject(0.0)
  }

  getExports() {
    this._api.get(`${Constants.API_ENDPOINT}/`).subscribe(
      (exports: Export[]) => this.exports.next(exports),
      (response: ApiErrorResponse) => {
        this.toastr.error(
          (response.error.message) ? response.error.message : response.message,
          (response.error.api_error) ? response.error.api_error : response.name,
          {timeOut: 0})
        console.error('api error:', response)
      },
      () => {
        console.info(`export service: ${this.exports.value.length} exports`)
        console.debug('exports:',  this.exports.value)
      }
    )
  }

  getCollections() {
    this._api.get(`${Constants.API_ENDPOINT}/Collections/`)
      .subscribe(
        (collections: Collection[]) => this.collections.next(collections),
        (response: ApiErrorResponse) => {
          this.toastr.error(
            (response.error.message) ? response.error.message : response.message,
            (response.error.api_error) ? response.error.api_error : response.name,
            {timeOut: 0})
        console.error('api error:', response)
      },
      () => {
        console.info(`export service: ${this.collections.value.length} collections`)
        console.debug('collections:',  this.collections.value)
      }
    )
  }

  downloadExport(x: Export, format: string) {
    let downloadExportURL = `${Constants.API_ENDPOINT}/${x.id}/${format}`
    let fileName = undefined

    let source = this._api.get(downloadExportURL, {
      headers: new HttpHeaders().set('Content-Type', `${FormatMapMime.get(format)}`),
      observe: 'events',
      responseType: 'blob',
      reportProgress: true,
    })
    let subscription = source.subscribe(
      event => {
        switch(event.type) {
          case(HttpEventType.DownloadProgress):
            if (event.hasOwnProperty('total')) {
              const percentage = Math.round((100 / event.total) * event.loaded)
              this.downloadProgress.next(percentage)
            } else {
              const kb = (event.loaded / 1024).toFixed(2)
              this.downloadProgress.next(parseFloat(kb))
            }
            break

          case(HttpEventType.ResponseHeader):
            if (event.ok) {
              const disposition = event.headers.get('Content-Disposition')
              const match = disposition ? /filename="?([^"]*)"?;?/g.exec(disposition) : undefined;
              fileName = match && match.length > 1 ? match[1] : undefined;
            }
            break

          case(HttpEventType.Response):
            this._blob = new Blob([event.body], {type: event.headers.get('Content-Type')})
            break
        }
      },
      (response: ApiErrorResponse) => {
        this.toastr.error(
          (response.error.message) ? response.error.message : response.message,
          (response.error.api_error) ? response.error.api_error : response.name,
          {timeOut: 0})
        console.error('api error:', response)
      },
      () => {
        this.saveBlob(this._blob, fileName)
        subscription.unsubscribe()
      }
    )
  }

  saveBlob(blob, filename) {
    let link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.setAttribute('visibility', 'hidden')
    link.download = filename
    link.onload = function() { URL.revokeObjectURL(link.href) }
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}
