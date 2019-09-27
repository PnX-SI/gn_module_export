import {
  Component,
  OnInit
} from "@angular/core";
import {
  FormGroup,
  FormBuilder,
  Validators
} from "@angular/forms";
import { NgbModal, NgbModalRef, NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import { ToastrService } from "ngx-toastr";

import { AppConfig } from "@geonature_config/app.config";

import { ModuleConfig } from "../module.config";
import { Export, ExportService, ApiErrorResponse } from "../services/export.service";


import { NgbdModalEmailContent } from "./export-getmail.component";

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
  public emailTmp:string;

  constructor(
    private _exportService: ExportService,
    private _fb: FormBuilder,
    private modalService: NgbModal,
    private toastr: ToastrService,
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

  open(modal_id) {
    this._modalRef = this.modalService.open(modal_id);
  }

  openModalEmail() {
    return new Promise((resolve, reject) => {
      this.modalService.open(NgbdModalEmailContent).result.then((inputEmail) => {
        if (inputEmail.valid && inputEmail.value)
          this.emailTmp = inputEmail.value;
        resolve();
      }, () => {
        resolve();
      });
    });
  }


  selectFormat(id_export: number, export_download) {
    this._getOne(id_export);
    this.open(export_download);
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

      this.openModalEmail().then(() => {
        let emailparams = this.emailTmp ? {
          'email': this.emailTmp
        } : {};
        this._exportService.downloadExport(
          this._export,
          this.formatSelection.value,
          emailparams
        ).subscribe(
          response => {
            this.emailTmp = '';
            this.toastr.success(
              response && response.message ? response.message : ''
            )
          },
          (response: ApiErrorResponse) => {
            this.toastr.error(
              response.error.message ? response.error.message : response.message, {
                timeOut: 0
              }
            );
          }
        );
      })

    }
  }
  }
