export interface APIResponse<T> {
  status: number;
  error?: string;
  result?: T;
}

export interface MutateConfigVars {
  key: string;
  value: any;
}

export interface WebhookBase {
  name: string;
  base_id: number;
  service: string;
  url: string;
  content_fmt: string;
  valid: boolean;
  default_triggers: string[];
}

export interface Entry {
  id: number;
  show_id: number;
  state: string;
  episode: number;
  version: string;
  torrent_hash?: string;
  file_path?: string;
  created_manually: boolean;
  last_update: string;
}

export interface Webhook {
  show_id: number;
  triggers: string[];
  base: WebhookBase;
}

export interface Metadata {
  show_id: number;
  kitsu_id?: number;
  slug?: string;
  status?: string;
  html_status?: string;
  poster?: string;
  link?: string;
}

export interface Show {
  id_: number;
  title: string;
  desired_format: string | null;
  desired_folder: string | null;
  season: number;
  episode_offset: number;
  watch: boolean;
  post_process: boolean;
  preferred_resolution: string | null;
  preferred_release_group: string | null;
  created_at: string;
  metadata: Metadata;
  entries: Entry[];
  webhooks: Webhook[];
}

export interface NyaaIndividualResult {
  show_id?: number;
  title: string;
  post_link: string;
  torrent_link: string;
  size: string;
  published: string;
  seeders: number;
  leechers: number;
}

export interface NyaaSearchResult {
  status: number;
  result: NyaaIndividualResult[];
}

export interface GeneralConfig {
  host?: string;
  port?: number;
  polling_interval?: number;
  complete_check_interval?: number;
  fuzzy_cutoff?: number;
  update_do_check?: boolean;
  locale?: string;
  log_level?: string;
  default_desired_folder?: string;
  default_desired_format?: string;
  unwatch_when_finished?: boolean;
}
