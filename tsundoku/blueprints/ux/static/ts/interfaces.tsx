export interface WebhookBase {
    name: string;
    base_id: number;
    service: string;
    url: string;
    content_fmt: string;
    valid: boolean;
}

export interface Entry {
    id: number;
    show_id: number;
    state: string;
    episode: number;
    torrent_hash?: string;
    file_path?: string;
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
    desired_format: string;
    desired_folder: string;
    season: number;
    episode_offset: number;
    watch: boolean;
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
