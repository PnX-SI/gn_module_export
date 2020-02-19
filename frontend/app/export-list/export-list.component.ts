import { Component, OnInit } from "@angular/core";
import { FormGroup, FormBuilder, Validators } from "@angular/forms";
import { NgbModal, NgbModalRef } from "@ng-bootstrap/ng-bootstrap";
import { CommonService } from "@geonature_common/service/common.service";
import { AppConfig } from "@geonature_config/app.config";

import { ModuleConfig } from "../module.config";
import {
  Export,
  ExportService,
  ApiErrorResponse
} from "../services/export.service";

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
  private _emailPattern = "^[a-z0-9._%+-]+@[a-z0-9.-]+.[a-z]{2,4}$";

  constructor(
    private _exportService: ExportService,
    private _fb: FormBuilder,
    private modalService: NgbModal,
    private _commonService: CommonService
  ) {}

  ngOnInit() {
    this.modalForm = this._fb.group({
      formatSelection: ["", Validators.required],
      exportLicence: ["", Validators.required],
      emailInput: ["", Validators.pattern[this._emailPattern]]
    });

    this.loadingIndicator = true;

    this._exportService.getExports().subscribe(
      (exports: Export[]) => {
        this.exports = exports;
        this.loadingIndicator = false;
      },
      (errorMsg: ApiErrorResponse) => {
        this._commonService.regularToaster(
          "error",
          errorMsg.error.message ? errorMsg.error.message : errorMsg.message
        );
        this.loadingIndicator = false;
      }
    );
  }

  get formatSelection() {
    return this.modalForm.get("formatSelection");
  }

  open(modal_id) {
    this._modalRef = this.modalService.open(modal_id);
  }

  selectFormat(id_export: number, export_download) {
    this._getOne(id_export);
    this.open(export_download);
  }

  _getOne(id_export: number) {
    this._export = this.exports.find((item: Export) => {
      return item.id === id_export;
    });
  }

  download() {
    if (this.modalForm.valid && this._export.id) {
      this.downloading = !this.downloading;

      this._modalRef.close();

      const emailparams = this.modalForm.get("emailInput").value
        ? { email: this.modalForm.get("emailInput").value }
        : {};

      this._exportService
        .downloadExport(this._export, this.formatSelection.value, emailparams)
        .subscribe(
          response => {
            this._commonService.regularToaster(
              "success",
              response && response.message ? response.message : ""
            );
          },
          (response: ApiErrorResponse) => {
            this._commonService.regularToaster(
              "error",
              response.error.message ? response.error.message : response.message
            );
          }
        );
    }
  }

  ngOnDestroy() {
    if (this._modalRef) {
      this._modalRef.close();
    }
  }
}
