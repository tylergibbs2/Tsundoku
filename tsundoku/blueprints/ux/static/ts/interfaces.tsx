interface WebhookBase {
    name: string;
    base_id: number;
    service: string;
    url: string;
    content_fmt: string;
    valid: boolean;
}

interface Entry {
    id: number;
    show_id: number;
    state: string;
    episode: number;
    torrent_hash?: string;
    file_path?: string;
    last_update: string;
}

interface Webhook {
    show_id: number;
    triggers: string[];
    base: WebhookBase;
}


interface Metadata {
    show_id: number;
    kitsu_id?: number;
    slug?: string;
    status?: string;
    html_status?: string;
    poster?: string;
    link?: string;
}


interface Show {
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

interface NyaaIndividualResult {
    show_id?: number;
    title: string;
    post_link: string;
    torrent_link: string;
    size: string;
    published: string;
    seeders: number;
    leechers: number;
}

interface NyaaSearchResult {
    status: number;
    result: NyaaIndividualResult[];
}

export {
    Show,
    Entry,
    Webhook,
    WebhookBase,
    NyaaIndividualResult,
    NyaaSearchResult
}
