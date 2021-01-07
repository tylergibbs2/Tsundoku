interface PartialEntry {
    id: number,
    show_id: number,
    current_state: string,
    episode: number
}

interface WebhookBase {
    name: string,
    base_id: number,
    service: string,
    url: string,
    content_fmt: string,
    valid: boolean
}

interface Webhook {
    wh_id: number,
    show_id: number,
    triggers: string[],
    base: WebhookBase
}

interface Show {
    id: number,
    title: string,
    desired_format: string,
    desired_folder: string,
    season: number,
    episode_offset: number,
    kitsu_id: number,
    entries: PartialEntry[],
    webhooks: Webhook[]
}