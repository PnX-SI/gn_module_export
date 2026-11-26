import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import {
  HttpClient,
  HttpClientModule,
  HttpClientXsrfModule,
  HTTP_INTERCEPTORS,
} from '@angular/common/http';
import { GN2CommonModule } from '@geonature_common/GN2Common.module';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { TranslateModule, TranslateLoader, TranslateService } from '@ngx-translate/core';
import { I18nService } from '@geonature/shared/translate/i18n-service';
import { ConfigService } from '@geonature/services/config.service';
import { CustomTranslateLoader } from '@geonature/shared/translate/custom-loader';
// import { NgbModalBackdrop } from "@ng-bootstrap/ng-bootstrap/modal/modal-backdrop";

import { ExportListComponent } from './export-list/export-list.component';

import { ExportService } from './services/export.service';

const routes: Routes = [{ path: '', component: ExportListComponent }];

// without this loader the module's assets/i18n is never read
export function createTranslateLoader(http: HttpClient, config: ConfigService) {
  return new CustomTranslateLoader(http, config, { moduleName: 'exports' });
}

@NgModule({
  imports: [
    HttpClientXsrfModule.withOptions({
      cookieName: 'token',
      headerName: 'token',
    }),
    CommonModule,
    ClipboardModule,
    GN2CommonModule,
    NgbModule,
    RouterModule.forChild(routes),
    TranslateModule.forChild({
      loader: {
        provide: TranslateLoader,
        useFactory: createTranslateLoader,
        deps: [HttpClient, ConfigService],
      },
      isolate: true,
    }),
  ],
  declarations: [ExportListComponent],
  providers: [ExportService],
  bootstrap: [],
})
export class GeonatureModule {
  constructor(
    private translateService: TranslateService,
    private i18nService: I18nService
  ) {
    // Workaround to force translation loaded for LazyModule.
    // See: https://github.com/ngx-translate/core/issues/1302
    this.i18nService.initializeModuleTranslateService(this.translateService);
  }
}
