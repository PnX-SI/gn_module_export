import {Injectable} from '@angular/core';
import { AppConfig } from '@geonature_config/app.config'


@Injectable()
export class Constants {

  public static readonly API_ENDPOINT = `${AppConfig.API_ENDPOINT}/exports`

}
