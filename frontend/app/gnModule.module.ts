import { NgModule } from '@angular/core'
import { CommonModule } from '@angular/common'
import { Routes, RouterModule } from '@angular/router'
import {
  HttpClientModule,
  HttpClientXsrfModule,
  HTTP_INTERCEPTORS
} from '@angular/common/http'
import { GN2CommonModule } from '@geonature_common/GN2Common.module'
import { TranslateHttpLoader } from '@ngx-translate/http-loader'
import { TreeModule } from 'angular-tree-component'
import {
  ExportListComponent,
  NgPBar,
  CollectionsComponent
} from './export-list/export-list.component'
import { ExportService } from './services/export.service'

const routes: Routes = [
  { path: '', component: ExportListComponent }
]

@NgModule({
  imports: [
    TreeModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'token',
      headerName: 'token'
    }),
    CommonModule,
    GN2CommonModule,
    RouterModule.forChild(routes)
  ],
  declarations: [
    ExportListComponent,
    NgPBar,
    CollectionsComponent
  ],
  providers: [
    ExportService,
  ],
  bootstrap: []
})

export class GeonatureModule {

}
