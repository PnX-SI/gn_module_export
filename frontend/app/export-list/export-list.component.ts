import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { CommonService } from '@geonature_common/service/common.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { ConfigService } from '@geonature/services/config.service';
import { map } from 'rxjs/operators';
import { Export, ExportService, ApiErrorResponse } from '../services/export.service';

import { UserDataService } from '@geonature/userModule/services/user-data.service';
@Component({
  selector: 'pnx-export-list',
  templateUrl: 'export-list.component.html',
  styleUrls: ['./export-list.component.scss'],
  providers: [],
})
export class ExportListComponent implements OnInit {
  exports: Export[];
  public api_endpoint = null;
  public modalForm: FormGroup;
  public buttonDisabled = false;
  public downloading = false;
  public loadingIndicator = false;
  public closeResult: string;
  public isDiplayedToken: boolean = false;
  public objectToken: { token: string; display: boolean }[] = [];

  private _export: Export;
  private _modalRef: NgbModalRef;
  public exportFormat: {} = null;
  private currentUser: User;
  private _fullUser: {};

  constructor(
    private _exportService: ExportService,
    private _fb: FormBuilder,
    private modalService: NgbModal,
    private _commonService: CommonService,
    private _userService: UserDataService,
    public _authService: AuthService,
    public config: ConfigService
  ) {
    this.exportFormat = this.config.EXPORTS['export_format_map'];
    this.api_endpoint = `${this.config.API_ENDPOINT}/${this.config.EXPORTS.MODULE_URL}`;
  }

  ngOnInit() {
    this.modalForm = this._fb.group({
      formatSelection: ['', Validators.required],
      exportLicence: ['', Validators.required],
    });

    this.currentUser = this._authService.getCurrentUser();

    this.loadingIndicator = true;

    this._exportService
      .getExports()
      .pipe(
        map((exports: Export[]) => {
          exports.forEach((element) => {
            element.cor_roles_exports.splice(1);
          });
          return exports;
        })
      )
      .subscribe(
        (exports: Export[]) => {
          // exports.forEach((element)=>{this.listToken.push(element.cor_roles_exports[0],false)})
          exports.forEach((element) => {
            element.cor_roles_exports.length > 0
              ? this.objectToken.push({ token: element.cor_roles_exports[0].token, display: false })
              : this.objectToken.push({ token: null, display: false });
          });
          this.exports = exports;
          //Chargement des données de l'utilisateur
          this._userService.getRole(parseInt(this.currentUser.id_role)).subscribe((res) => {
            this._fullUser = res;
            this.modalForm.patchValue({ emailInput: this._fullUser['email'] });
            this.loadingIndicator = false;
          });
        },
        (errorMsg: ApiErrorResponse) => {
          this._commonService.regularToaster(
            'error',
            errorMsg.error.message ? errorMsg.error.message : errorMsg.message
          );
          this.loadingIndicator = false;
        }
      );
  }

  get formatSelection() {
    return this.modalForm.get('formatSelection');
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

      this._exportService.downloadExport(this._export, this.formatSelection.value).subscribe(
        (response) => {
          this._commonService.regularToaster(
            'success',
            response && response.message ? response.message : ''
          );
        },
        (response: ApiErrorResponse) => {
          this._commonService.regularToaster(
            'error',
            response.error.message ? response.error.message : response.message
          );
        }
      );
    }
  }

  cancel_download() {
    // Annulation de l'action export (close modal)
    this._modalRef.close();
  }

  copyToken(val: string, index_token: string) {
    const selBox = document.createElement('textarea');
    selBox.style.position = 'fixed';
    selBox.style.left = '0';
    selBox.style.top = '0';
    selBox.style.opacity = '0';
    selBox.value = val;
    document.body.appendChild(selBox);
    selBox.focus();
    selBox.select();
    document.execCommand('copy');
    document.body.removeChild(selBox);
    this.objectToken[index_token].display = true;
  }

  ngOnDestroy() {
    if (this._modalRef) {
      this._modalRef.close();
    }
  }
}
