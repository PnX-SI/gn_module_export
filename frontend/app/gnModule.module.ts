import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Routes, RouterModule } from "@angular/router";
import { HttpClientModule } from "@angular/common/http";
import { GN2CommonModule } from "@geonature_common/GN2Common.module";
import { TranslateHttpLoader } from "@ngx-translate/http-loader";
import { ExportsListComponent, NgPBar } from "./exports-list/exports-list.component";
import { ExportService } from "./services/export.service";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";
import { NgbModalStack } from "@ng-bootstrap/ng-bootstrap/modal/modal-stack";
import { NgbModalWindow } from "@ng-bootstrap/ng-bootstrap/modal/modal-window";
import { NgbModalBackdrop } from "@ng-bootstrap/ng-bootstrap/modal/modal-backdrop";

const routes: Routes = [
  { path: "", component: ExportsListComponent }
];

@NgModule({
  imports: [
    HttpClientModule,
    CommonModule,
    GN2CommonModule,
    RouterModule.forChild(routes)
  ],
  declarations: [
    ExportsListComponent,
    // NgbModalBackdrop,
    // NgbModalWindow,
    NgPBar
  ],
  providers: [
    ExportService, 
    // NgbModal,
    // NgbModalWindow,
    // NgbModalStack
  ],
  bootstrap: []
})

export class GeonatureModule {

}
