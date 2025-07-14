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

export interface EntryEncodeInfo {
  initial_size: number;
  final_size: number;
  queued_at: string;
  started_at: string;
  ended_at: string;
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

export interface Library {
  id_: number;
  folder: string;
  is_default: boolean;
}

export interface Show {
  id_: number;
  library_id: number;
  title: string;
  title_local: string | null;
  desired_format: string | null;
  season: number;
  episode_offset: number;
  watch: boolean;
  preferred_resolution: string | null;
  preferred_release_group: string | null;
  created_at: string;
  metadata: Metadata;
  entries: Entry[];
  webhooks: Webhook[];
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface PaginatedShowsResponse {
  shows: Show[];
  pagination: PaginationInfo;
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
  default_desired_format: string;
  unwatch_when_finished?: boolean;
  use_season_folder?: boolean;
}

export interface SeenRelease {
  title: string;
  release_group: string;
  episode: number;
  resolution: string;
  version: string;
  torrent_destination: string;
  seen_at: string;
}

export interface TreeResponse {
  root_is_writable: boolean;
  can_go_back: boolean;
  current_path: string;
  children: string[];
}
