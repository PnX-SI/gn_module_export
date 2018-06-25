import {
  Component,
  Renderer2,
  ViewChild,
  Pipe,
  PipeTransform
} from "@angular/core";
import { DatePipe } from '@angular/common';
import {
  FormControl,
  FormGroup,
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  Validators
} from "@angular/forms";
import { Router } from "@angular/router";
import { Observable } from "rxjs/Observable";
import { TranslateService } from "@ngx-translate/core";
import { NgbModal, ModalDismissReasons } from "@ng-bootstrap/ng-bootstrap";
import { CommonService } from "@geonature_common/service/common.service";
import { DynamicFormComponent } from "@geonature_common/form/dynamic-form/dynamic-form.component";
import { DynamicFormService } from "@geonature_common/form/dynamic-form/dynamic-form.service";
import { Export, ExportService, ExportLabel, StandardMap } from "../services/export.service";



@Component({
  selector: 'ng-pbar',
  template: `<p><ngb-progressbar type="info" [value]="progress$ | async" [striped]="true" [animated]="true"></ngb-progressbar></p>`
})
export class NgPBar {
  progress$: Observable<number>

  constructor(private _exportService: ExportService) {
    this.progress$ = this._exportService.downloadProgress
  }
}

@Component({
  selector: "pnx-exports-list",
  templateUrl: "exports-list.component.html",
  styleUrls: ["./exports-list.component.scss"],
  providers: []
})
export class ExportsListComponent {
  exports$: Observable<Export[]>
  exportLabels$: Observable<ExportLabel[]>
  public modalForm : FormGroup;
  public buttonDisabled: boolean = false;
  public barHide: boolean = false;
  public closeResult: string;

  constructor(
    private _exportService: ExportService,
    private _commonService: CommonService,
    private _translate: TranslateService,
    private _router: Router,
    private modalService: NgbModal,
    private _fb: FormBuilder,
    private _dynformService: DynamicFormService) {

    this.modalForm = this._fb.group({
      adresseMail:['', Validators.compose([Validators.required, Validators.email])],
      chooseFormat:['', Validators.required],
      chooseStandard:['', Validators.required]
    });

    this._exportService.getExports();
    this.exports$ = this._exportService.exports;
    this.exportLabels$ = this._exportService.labels
  }

  get chooseFormat() {
    return this.modalForm.get('chooseFormat');
  }

  get chooseStandard() {
    return this.modalForm.get('chooseStandard');
  }

  //Fonction pour envoyer un mail à l'utilisateur lorsque le ddl est terminé.
  get adresseMail() {
    return this.modalForm.get('adresseMail');
  }

  open(content) {
    this.modalService.open(content).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    });
  }

  private getDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return `with: ${reason}`;
    }
  }

  //Fonction qui bloque le boutton de validation tant que la licence n'est pas checkée
  follow() {
    this.buttonDisabled = !this.buttonDisabled;
  }

  showme() {
    this.barHide = !this.barHide;
    if (this.barHide) {
      const choice = window.document.querySelector('input[name="options"]:checked');
      const standard = StandardMap.get(this.chooseStandard.value)
      const extension = this.chooseFormat.value
      this.exports$.switchMap(
        (exports: Export[]) => exports.sort((a, b) => (a.id < b.id) ? 1 : (a.id > b.id) ? -1 : 0)
                                      .filter(
          (x: Export) => (x.label == choice.id && x.extension == extension))  // FIXME: get latest
      ).subscribe(
        x => this._exportService.downloadExport(parseFloat(x.id), x.label, extension),
        e => console.error(e.message)
      )
    }
  }

  //Fonction pour avoir un modal vierge si l'on ferme puis réouvre le modal
  resetModal() {
    this.modalForm.reset();
  }
}
