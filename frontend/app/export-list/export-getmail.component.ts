import {
    Component,
    OnInit
} from "@angular/core";
import {
    FormGroup,
    FormBuilder,
    Validators
} from "@angular/forms";
import {
    NgbModal,
    NgbModalRef,
    NgbActiveModal
} from "@ng-bootstrap/ng-bootstrap";



@Component({
    template: `
    <!-- Modal Email-->
     <div class="modal-content">
       <!-- Modal content-->
       <div class="modal-header">
           <h4 class="modal-title">Configuration export</h4>
       </div>

       <div class="modal-body">
        <div>
          <p>Entrez un email pour réceptionner le lien de téléchargement vers l'export demandé.</p>
        </div>
         <!-- Formulaire de récupération d'email pour la réception du lien de téléchargement -->
         <form [formGroup]="modalFormEmail">
            <label for="emailInput" >Email</label>
           <input type="email" formControlName="emailInput" [(ngModel)]="emailTmp" id="emailInput" class="form-control" />
           <div *ngIf="emailInput.errors?.email">
              Email not valid.
          </div>
         </form>

       </div>
       <!-- Bouton de fermeture de la modal pop-up ou lancement du téléchargement avec email temporaire -->
       <div class="modal-footer" >
         <button type="submit" class="btn btn-danger" data-dismiss="modal" (click)="modal.dismiss()">Annuler</button>
         <button [disabled]="!modalFormEmail.valid" type="submit" class="btn btn-success" (click)="modal.close(emailInput)">OK</button>
       </div>
     </div>
    `
})
export class NgbdModalEmailContent {
    public modalFormEmail: FormGroup;
    public emailTmp: string = "";
    constructor(
        private _modalService: NgbModal,
        public modal: NgbActiveModal,
        private _fb: FormBuilder,
    ) {}
    ngOnInit() {

        this.modalFormEmail = this._fb.group({
            emailInput: ["", Validators.email],
        });
    }

    open() {
        this.modal = this._modalService.open();
    }

    get emailInput() {
        return this.modalFormEmail.get('emailInput');
    }

    getEmail(emailForm) {
        console.log("value: ", emailForm.value);
        this.modal.close(emailForm);
    }
}