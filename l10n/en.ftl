## General

page-title = 積ん読 ANIME

category-general = General
page-shows = Shows
page-nyaa = Nyaa Search

category-settings = Settings
page-webhooks = Webhooks
page-config = Config
page-logs = Logs

logout-button = Logout

entry-status-downloading = Downloading
entry-status-downloaded = Downloaded
entry-status-renamed = Renamed
entry-status-moved = Moved
entry-status-completed = Completed
entry-status-buffered = Buffered
entry-status-failed = Failed

watch-button-title = Watch
unwatch-button-title = Unwatch

process-button-title = Enable Post-Processing
unprocess-button-title = Disable Post-Processing

delete-confirm-text = Are you sure you want to delete <b>{$name}</b>?
delete-cancel = No, take me back

-action-edit = Edit
-action-delete = Delete

## Errors

no-rss-parsers = No RSS sources installed.
no-shows-found = No shows found, is there an error with your sources?
dl-client-connection-error = There was an error connecting to the download client.

## Index Page

shows-page-title = { page-shows }
shows-page-subtitle = Tracked shows in RSS

status-current = Airing
status-finished = Finished
status-tba = TBA
status-unreleased = Unreleased
status-upcoming = Upcoming

show-edit-link = { -action-edit }
show-delete-link = { -action-delete }

show-add-success = Show successfully added.
show-update-success = Show successfully updated.
show-delete-success = Show successfully removed.

empty-show-container = Nothing to see here!
empty-show-container-help = Begin by adding a show below.

click-for-more-shows =
    Click to see {{ $not_shown }} more {$not_shown ->
        [one] item
        *[other] items
    }...
back-to-top-link = Back to Top

add-show-button = Add show

add-modal-header = Add Show

add-form-discover-select-title = Please select a show title...
add-form-discover-select-release-group = Please select a release group...
add-form-discover-select-resolution = Please select a resolution...

add-form-discover-mode-result-amount =
    Upon adding, { $releaseCount } already seen {$releaseCount ->
        [one] release
        *[other] releases
    } will begin processing.

add-form-discover-mode-seen-episodes = Seen Episodes

add-form-mode-manual = Manual Mode
add-form-mode-discover = Discover Mode

add-form-name-tt = Name of the title as it appears in the RSS feed.
add-form-name-field = Name
add-form-name-placeholder = Attack on Titan

add-form-desired-format-tt = Desired name of the file after it is renamed.
add-form-desired-format-field = Desired Format

add-form-season-tt = Value to use for the season of the series when renaming.
add-form-season-field = Season

add-form-episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.
add-form-episode-offset-field = Episode Offset

add-form-library-tt = Which library to move entries from this show to
add-form-library-field = Library

add-form-advanced = Advanced Settings

add-form-local-title-tt = Override the title of the show when moving and renaming
add-form-local-title-field = Local Title Override

add-form-add-button = Add show
add-form-cancel-button = Cancel

delete-modal-header = Delete Show

edit-modal-header = Edit Show
edit-clear-cache = Clear Cache
edit-fix-match = Fix Match
edit-kitsu-id = Kitsu.io Show ID

edit-tab-info = Information
edit-tab-entries = Entries
edit-tab-webhooks = Webhooks

edit-entries-th-episode = Episode
edit-entries-th-status = Entry Status
edit-entries-th-last-update = Updated
edit-entries-th-encode-status = Encode Status

edit-entries-is-empty = No entries yet!
edit-entries-last-update = {$time} ago

edit-entries-encode-status-notqueued = Not Queued
edit-entries-encode-status-queued = Queued
edit-entries-encode-status-encoding = Encoding
edit-entries-encode-status-finished = Finished
edit-entries-encode-status-unknown = Unknown

edit-entries-form-episode = Episode
edit-entries-form-magnet = Magnet URL
edit-entries-form-exists = This episode is already tracked.
edit-entries-form-add-button = Add entry

edit-webhooks-th-webhook = Webhook
edit-webhooks-th-failed = Failed
edit-webhooks-th-downloading = Downloading
edit-webhooks-th-downloaded = Downloaded
edit-webhooks-th-renamed = Renamed
edit-webhooks-th-moved = Moved
edit-webhooks-th-completed = Completed

edit-webhooks-is-empty = Add webhooks on the webhooks page.

edit-form-name-tt = Name of the title as it appears in the RSS feed.
edit-form-name-field = Name
edit-form-name-placeholder = Show title

edit-form-resolution-tt = The resolution to download for this show.
edit-form-resolution-field = Preferred Resolution

edit-form-release-group-tt = The release group to look for releases from.
edit-form-release-group-field = Preferred Release Group

edit-form-advanced = Advanced Settings

edit-form-desired-format-tt = Override the global format used to rename the completed file.
edit-form-desired-format-field = File Format Override

edit-form-desired-folder-tt = Override the global folder to place the completed file.
edit-form-desired-folder-field = Folder Placement Override

edit-form-season-tt = Value to use for the season of the series when renaming.
edit-form-season-field = Season

edit-form-episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.
edit-form-episode-offset-field = Episode Offset

edit-form-library-tt = Which library to move entries from this show to
edit-form-library-field = Library

edit-form-local-title-tt = Override the title of the show when moving and renaming
edit-form-local-title-field = Local Title Override

edit-form-cancel-button = Cancel

list-view-actions-header = Actions
list-view-entry-update-header = Last Update

sort-by-header = Sort By
sort-dir-asc = Asc
sort-dir-desc = Desc
sort-key-title = Title
sort-key-update = Last Update
sort-key-date-added = Date Added

pagination-previous = Previous
pagination-next = Next
pagination-showing = Showing
pagination-of = of
pagination-items = items

## Configuration Page

config-page-title = Configuration
config-page-subtitle = Update app settings and general configuration

config-test = Test
config-test-success = Connected
config-test-failure = Error connecting

feedback-request = Request a Feature
feedback-bug = Report a Bug

section-general-title = General
section-general-subtitle = General app settings and configuration

section-libraries-title = Libraries
section-libraries-subtitle = File paths where downloads are moved to

libraries-th-directory = Directory
libraries-th-actions = Actions

libraries-td-set-default = Set Default
libraries-td-default = Default

libraries-delete-success = Library deleted successfully.
libraries-update-success = Library updated successfully.

general-host-title = Server Host
general-host-tooltip = Changes require application restart
general-host-subtitle = Address and port to bind to

general-loglevel-title = Log Level
general-loglevel-subtitle = Severity level at which to log

general-locale-title = Locale
general-locale-tooltip = Updates on page refresh
general-locale-subtitle = The language that the app displays

general-updatecheck-title = Update Check
general-updatecheck-tooltip = Checks daily
general-updatecheck-subtitle = Whether or not to periodically check for updates

general-defaultformat-title = File Name Format
general-defaultformat-subtitle = The format to use when naming the completed file

general-unwatchfinished-title = Unwatch When Finished
general-unwatchfinished-subtitle = Unwatch shows after they are marked as finished

seconds-suffix = seconds

section-feeds-title = Feeds
section-feeds-subtitle = Polling intervals and cutoff for RSS feeds

feeds-fuzzy-cutoff-title = Fuzzy Cutoff
feeds-fuzzy-cutoff-subtitle = Cutoff for matching show names

feeds-pollinginterval-title = Polling Interval
feeds-pollinginterval-tooltip = Setting this to a low number may get you blocked from certain RSS feeds
feeds-pollinginterval-subtitle = Frequency for checking RSS feeds

feeds-completioncheck-title = Completion Check Interval
feeds-completioncheck-subtitle = Frequency for checking completion status

feeds-seedratio-title = Seed Ratio Limit
feeds-seedratio-subtitle = Wait for this seed ratio before processing a download

section-torrent-title = Torrent Client
section-torrent-subtitle = For connecting to a download client

torrent-client-title = Client
torrent-client-subtitle = Which torrent client to use

torrent-host-title = Client Host
torrent-host-subtitle = The location the client is hosted at

torrent-username-title = Username
torrent-username-subtitle = Authentication username

torrent-password-title = Password
torrent-password-subtitle = Authentication password

torrent-secure-title = Secure
torrent-secure-subtitle = Connect on HTTPS

section-api-title = API Key
section-api-subtitle = For third-party integration with Tsundoku

api-key-refresh = Refresh
config-api-documentation = Documentation

section-encode-title = Post-processing
section-encode-subtitle = Encoding of completed downloads for lower file sizes

process-quality-title = Quality Preset
process-quality-subtitle = Higher quality will result in larger file sizes

encode-stats-total-encoded = {$total_encoded} Completed Encodes
encode-stats-total-saved-gb = {$total_saved_gb} Total GB Saved
encode-stats-avg-saved-mb = {$avg_saved_mb} Average MB Saved
encode-stats-median-time-hours = {$median_time_hours} Median Hours Spent
encode-stats-avg-time-hours = {$avg_time_hours} Average Hours Spent

encode-quality-low = Low
encode-quality-moderate = Moderate
encode-quality-high = High

encode-quality-low-desc = actually really bad
encode-quality-moderate-desc = meh
encode-quality-high-desc = visually lossless

process-speed-title = Speed Preset
process-speed-subtitle = Faster speeds will result in lower quality and larger file sizes

encode-speed-ultrafast = Ultra Fast
encode-speed-superfast = Super Fast
encode-speed-veryfast = Very Fast
encode-speed-faster = Faster
encode-speed-fast = Fast
encode-speed-medium = Medium
encode-speed-slow = Slow
encode-speed-slower = Slower
encode-speed-veryslow = Very Slow

encode-encoder-title = Encoder
encode-encoder-subtitle = Which video codec to re-encode to

process-max-encode-title = Maximum Active Encodes
process-max-encode-subtitle = Number of possible concurrent encode operations

process-minimum-file-size-title = Minimum File Size
process-minimum-file-size-subtitle = Do not encode if the file is below this size

process-mfs-no-minimum = No Minimum File Size

checkbox-enabled = Enabled
ffmpeg-missing = FFmpeg Not Installed

encode-time-title = Encoding Time
encode-time-subtitle = Time range in which encoding should take place

hour-0 = Midnight
hour-1 = 1 am
hour-2 = 2 am
hour-3 = 3 am
hour-4 = 4 am
hour-5 = 5 am
hour-6 = 6 am
hour-7 = 7 am
hour-8 = 8 am
hour-9 = 9 am
hour-10 = 10 am
hour-11 = 11 am
hour-12 = Noon
hour-13 = 1 pm
hour-14 = 2 pm
hour-15 = 3 pm
hour-16 = 4 pm
hour-17 = 5 pm
hour-18 = 6 pm
hour-19 = 7 pm
hour-20 = 8 pm
hour-21 = 9 pm
hour-22 = 10 pm
hour-23 = 11 pm

## Login Page

form-missing-data = Login Form missing required data.
invalid-credentials = Invalid username and password combination.

username = Username
password = Password

remember-me = Remember me
login-button = Login

## Register Page

form-register-missing-data = Form missing required field '{{ $field }}'.
form-password-mismatch = Passwords do not match.
form-password-characters = Password must be at least 8 characters.
form-username-taken = A user with the username already exists.

form-register-success = You have successfully registered, please login.

confirm-password = Confirm Password

register-button = Register

## Logs Page

logs-page-title = Logs
logs-page-subtitle = Activity that is currently going on within the app

logs-download = Download Logs

log-level-info = Info
log-level-warning = Warning
log-level-error = Error
log-level-debug = Debug

title-with-episode = {$title}, episode {$episode}
episode-prefix-state = Episode {$episode}, {$state}

context-cache-failure = [Item not Cached ({$type}{$id})]

websocket-state-connecting = Connecting
websocket-state-connected = Connected
websocket-state-disconnected = Disconnected

## Webhooks Page

webhooks-page-title = Webhooks
webhooks-page-subtitle = Usable by your tracked shows

webhook-status-valid = 🟢 Connected
webhook-status-loading = 🟡 Loading...
webhook-status-invalid = 🔴 Connection Error

webhook-add-success = Webhook added successfully!
webhook-edit-success = Webhook updated successfully!
webhook-delete-success = Webhook deleted successfully!

webhook-edit-link = Edit
webhook-delete-link = Delete

webhook-page-empty = Nothing to see here!
webhook-page-empty-subtitle = Begin by adding a webhook below.

webhook-add-button = Add webhook

add-webhook-modal-header = Add Webhook

add-webhook-form-name-tt = Name of the webhook, only for display purposes.
add-webhook-form-name-field = Name
add-webhook-form-name-placeholder = My Webhook

add-webhook-form-service-tt = The service that the webhook posts to.
add-webhook-form-service-field = Service

add-webhook-form-url-tt = URL that the webhook posts to.
add-webhook-form-url-field = URL

add-webhook-form-content-tt = The format that the content will be sent in.
add-webhook-form-content-field = Content Format

add-webhook-form-default-triggers-tt = Triggers that will be enabled by default with new shows.
add-webhook-form-default-triggers-field = Default Triggers

add-webhook-form-add-button = Add webhook
add-webhook-form-cancel-button = Cancel

delete-webhook-modal-header = Delete Webhook
delete-confirm-button = Delete

edit-webhook-modal-header = Edit Webhook

edit-form-save-button = Save changes

## Nyaa Search Page

nyaa-page-title = Nyaa Search
nyaa-page-subtitle = Search for anime releases

entry-add-success = Successfully added release! Processing {$count} new {$count ->
        [one] entry
        *[other] entries
    }.

search-placeholder = Attack on Titan
search-empty-results = Nothing to see here!
search-start-searching = Start searching to see some results.

search-th-name = Name
search-th-size = Size
search-th-date = Date
search-th-seeders = Seeders
search-th-leechers = Leechers
search-th-link = Link to Post

search-item-link = Link

modal-title = Add Search Result
modal-tab-new = New Show
modal-tab-existing = Add to Existing

existing-show-tt = Existing show you want to add this release to.
existing-show-field = Show

name-tt = Name of the title as it appears in the RSS feed.
name-field = Name
name-placeholder = Show title

desired-format-tt = Desired name of the file after it is renamed.
desired-format-field = Desired Format

desired-folder-tt = Folder which to place the completed file.
desired-folder-field = Desired Folder

season-tt = Value to use for the season of the series when renaming.
season-field = Season

episode-offset-tt = Positive or negative value by which to modify the episode number as it appears in the RSS feed.
episode-offset-field = Episode Offset

add-button = Add release
cancel-button = Cancel