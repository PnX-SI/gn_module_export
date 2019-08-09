import {
  Component,
  OnInit,
  Input,
  ViewChild,
  ElementRef,
} from "@angular/core";
import {
  FormGroup,
  FormBuilder,
  Validators
} from "@angular/forms";
import { Router } from "@angular/router";
import { Observable } from "rxjs/Observable";
import { TranslateService } from "@ngx-translate/core";
import { NgbModal, NgbModalRef} from "@ng-bootstrap/ng-bootstrap";
import { ToastrService } from "ngx-toastr";
import { CommonService } from "@geonature_common/service/common.service";

import { AppConfig } from "@geonature_config/app.config";

import { ModuleConfig } from "../module.config";
import { Export, ExportService, ApiErrorResponse } from "../services/export.service";

@Component({
  selector: "download-progress-bar",
  template: `
    <div class="telechargement">{{ message }}</div>
    <p>
      <ngb-progressbar
        [type]="type"
        [value]="progress$ | async"
        [striped]="true"
        [animated]="animated"
      ></ngb-progressbar>
    </p>
  `
})
export class ProgressComponent {
  progress$: Observable<number>;
  @Input() message = "Téléchargement en cours...";
  @Input() type = "info";
  @Input() animated = true;

  constructor(private _exportService: ExportService) {}

  ngOnInit() {
    this.progress$ = this._exportService.downloadProgress;
    this.progress$.subscribe(state => (state === 100 ? this.done() : null));
  }

  done() {
    this.message = "Export téléchargé.";
    this.type = "success";
    this.animated = false;
  }
}

@Component({
  selector: "pnx-export-list",
  templateUrl: "export-list.component.html",
  styleUrls: ["./export-list.component.scss"],
  providers: []
})
export class ExportListComponent implements OnInit {
  exports: Export[];
  public api_endpoint = `${AppConfig.API_ENDPOINT}/${ModuleConfig.MODULE_URL}`;
  public modalForm: FormGroup;
  public buttonDisabled = false;
  public downloading = false;
  public loadingIndicator = false;
  public closeResult: string;
  private _export: Export;
  private _modalRef: NgbModalRef;


  constructor(
    private _exportService: ExportService,
    private _commonService: CommonService,
    private _translate: TranslateService,
    private _router: Router,
    private _fb: FormBuilder,
    private modalService: NgbModal,
    private toastr: ToastrService
  ) {}

  ngOnInit() {
    this.modalForm = this._fb.group({
      formatSelection: ["", Validators.required],
      exportLicence: ["", Validators.required]
    });

    this.loadingIndicator = true;

    this._exportService.getExports()
      .subscribe(
        (exports: Export[]) => {
          this.exports = exports;
          this.loadingIndicator = false;
        },
        (errorMsg: ApiErrorResponse) => {
          this.toastr.error(
            errorMsg.error.message ? errorMsg.error.message : errorMsg.message,
            errorMsg.error.api_error ? errorMsg.error.api_error : errorMsg.name,
            { timeOut: 0 }
          );
          console.error("api error:", errorMsg);
          this.loadingIndicator = false;
        },
      );


  }

  get formatSelection() {
    return this.modalForm.get("formatSelection");
  }

  open(content) {
    this._modalRef = this.modalService.open(content);
  }

  selectFormat(id_export: number, content) {
    this._getOne(id_export);
    this.open(content);
  }

  _getOne(id_export: number) {
    this._export = this.exports
    .find((item: Export) => {
     return item.id == id_export
    })

  }

  download() {
    if (this.modalForm.valid && this._export.id) {
      this.downloading = !this.downloading;
      this._modalRef.close();
      this._exportService.downloadExport(
        this._export,
        this.formatSelection.value
      ).subscribe(
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
      );
    }
  }
}
