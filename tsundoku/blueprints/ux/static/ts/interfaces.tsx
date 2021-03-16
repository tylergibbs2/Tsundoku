interface WebhookBase {
    name: string;
    base_id: number;
    service: string;
    url: string;
    content_fmt: string;
    valid: boolean;
}

interface PartialEntry {
    id: number;
    show_id: number;
    state: string;
    episode: number;
}

interface Webhook {
    wh_id: number;
    show_id: number;
    triggers: string[];
    base: WebhookBase;
}


interface Show {
    id_: number;
    title: string;
    desired_format: string;
    desired_folder: string;
    season: number;
    episode_offset: number;
    kitsu_id: number;
    entries: PartialEntry[];
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
    PartialEntry,
    Webhook,
    WebhookBase,
    NyaaIndividualResult,
    NyaaSearchResult
}