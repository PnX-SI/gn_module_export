import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Routes, RouterModule } from "@angular/router";
import {
  HttpClientModule,
  HttpClientXsrfModule,
  HTTP_INTERCEPTORS
} from "@angular/common/http";
import { GN2CommonModule } from "@geonature_common/GN2Common.module";
import { NgbModule } from "@ng-bootstrap/ng-bootstrap";

import { TranslateHttpLoader } from "@ngx-translate/http-loader";
// import { NgbModalBackdrop } from "@ng-bootstrap/ng-bootstrap/modal/modal-backdrop";

import { ExportListComponent } from "./export-list/export-list.component";

import { ExportService } from "./services/export.service";

const routes: Routes = [{ path: "", component: ExportListComponent }];

@NgModule({
  imports: [
    HttpClientXsrfModule.withOptions({
      cookieName: "token",
      headerName: "token"
    }),
    CommonModule,
    GN2CommonModule,
    NgbModule,
    RouterModule.forChild(routes)
  ],
  declarations: [ExportListComponent],
  providers: [ExportService],
  bootstrap: []
})
export class GeonatureModule {}
