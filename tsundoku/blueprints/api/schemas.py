from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from tsundoku.manager import Show

if TYPE_CHECKING:
    from tsundoku.nyaa import SearchResult

# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class TreeRequest(BaseModel):
    dir: str
    subdir: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class GeneralConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int | None = None
    update_do_check: bool | None = None
    locale: str | None = None
    log_level: str | None = None
    default_desired_format: str | None = None
    unwatch_when_finished: bool | None = None
    use_season_folder: bool | None = None


class FeedsConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    polling_interval: int | None = None
    complete_check_interval: int | None = None
    fuzzy_cutoff: int | None = None
    seed_ratio_limit: float | None = None


class TorrentConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    secure: bool | None = None


class ShowCreate(BaseModel):
    title: str
    title_local: str | None = None
    library_id: int
    desired_format: str | None = None
    season: int
    episode_offset: int = 0
    watch: bool = True
    preferred_resolution: str | None = None
    preferred_release_group: str | None = None


class ShowUpdate(BaseModel):
    title: str
    title_local: str | None = None
    library_id: int
    desired_format: str | None = None
    season: int | None = None
    episode_offset: int | None = None
    watch: bool | None = None
    kitsu_id: int | None = None
    preferred_resolution: str | None = None
    preferred_release_group: str | None = None


class EntryCreate(BaseModel):
    episode: int
    magnet: str | None = None


class WebhookUpdate(BaseModel):
    triggers: str = ""


class WebhookBaseCreate(BaseModel):
    name: str
    service: str
    url: str
    content_fmt: str | None = None
    default_triggers: str = ""


class WebhookBaseUpdate(BaseModel):
    name: str
    service: str
    url: str
    content_fmt: str | None = None
    default_triggers: str = ""


class SeenReleaseAddRequest(BaseModel):
    title: str
    release_group: str
    resolution: str


class NyaaShowRequest(BaseModel):
    show_id: int
    torrent_link: str
    overwrite: bool = False


class LibraryCreate(BaseModel):
    folder: str


class LibraryUpdate(BaseModel):
    folder: str
    is_default: bool = False


class IssueRequest(BaseModel):
    issue_type: str | None = None
    user_agent: str | None = None


# ---------------------------------------------------------------------------
# Response payloads that are shaped by the web layer rather than a single
# domain object. Domain models (Show, Entry, Library, ...) are returned
# directly elsewhere; these describe composite or derived responses.
# ---------------------------------------------------------------------------


class ShowEntryRecord(BaseModel):
    """The trimmed entry view returned by the per-show entry listing."""

    id: int
    episode: int
    current_state: str
    torrent_hash: str


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class ShowsPage(BaseModel):
    shows: list[Show]
    pagination: Pagination


class NyaaResult(BaseModel):
    show_id: int | None
    title: str
    published: str
    torrent_link: str
    post_link: str
    size: str
    seeders: int
    leechers: int

    @classmethod
    def from_search_result(cls, result: SearchResult) -> NyaaResult:
        return cls(
            show_id=result.show_id,
            title=result.title,
            published=result.published.strftime("%d %b %Y"),
            torrent_link=result.torrent_link,
            post_link=result.post_link,
            size=result.size,
            seeders=result.seeders,
            leechers=result.leechers,
        )


class SeenReleaseAddResult(BaseModel):
    additional: int
    episodes: list[int]


class TorrentTestResult(BaseModel):
    success: bool
    error: str | None = None


class DirectoryTree(BaseModel):
    root_is_writable: bool
    can_go_back: bool
    current_path: str
    children: list[str]


class GeneralConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    host: str
    port: int
    update_do_check: bool
    locale: str
    log_level: str
    default_desired_format: str
    unwatch_when_finished: bool
    use_season_folder: bool


class FeedsConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    polling_interval: int
    complete_check_interval: int
    fuzzy_cutoff: int
    seed_ratio_limit: float


class TorrentConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    client: str
    host: str
    port: int
    username: str | None
    password: str | None
    secure: bool
