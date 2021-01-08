var entriesToDelete = [];
var entriesToAdd = [];
var all_triggers = ["downloading", "downloaded", "renamed", "moved", "completed"];
var modalsCanBeClosed = true;
function showAddorEditProgressBars() {
    modalsCanBeClosed = false;
    $(".closes-modals").addClass("is-hidden");
    $(".submits-modals").addClass("is-hidden");
    $("progress").removeClass("is-hidden");
}
function hideAddorEditProgressBars() {
    modalsCanBeClosed = true;
    $(".closes-modals").removeClass("is-hidden");
    $(".submits-modals").removeClass("is-hidden");
    $("progress").addClass("is-hidden");
}
function updateTsundoku() {
    modalsCanBeClosed = false;
    $("#updating-pg-bar").removeClass("is-hidden");
    $("#update-button").addClass("is-hidden");
    $("#close-update-modal-button").addClass("is-hidden");
    $.ajax({
        url: "/update",
        type: "POST"
    });
    function poll() {
        setTimeout(function () {
            $.ajax({
                url: "/",
                type: "GET",
                success: function () {
                    location.reload();
                },
                statusCode: {
                    302: function (xhr) {
                        location.reload();
                    }
                },
                complete: function () {
                    poll();
                },
                timeout: 1000
            });
        }, 1000);
    }
    ;
    setTimeout(poll, 5000);
}
function submitAddOrEditShowForm(event) {
    showAddorEditProgressBars();
    event.preventDefault();
    var url = $(this).closest("form").attr("action");
    var method = $(this).closest("form").attr("method");
    var data = $(this).closest("form").serialize();
    updateWebhooks();
    for (var _i = 0, entriesToDelete_1 = entriesToDelete; _i < entriesToDelete_1.length; _i++) {
        var entry = entriesToDelete_1[_i];
        deleteShowEntry(entry[0], entry[1]);
    }
    for (var _a = 0, entriesToAdd_1 = entriesToAdd; _a < entriesToAdd_1.length; _a++) {
        var entry = entriesToAdd_1[_a];
        addShowEntry(entry[0], entry[1], entry[2]);
    }
    $.ajax({
        url: url,
        type: method,
        data: data,
        success: function (data) {
            location.reload();
        },
        error: function (jqXHR, status, error) {
            hideAddorEditProgressBars();
            alert("There was an error processing the request.");
        }
    });
}
function updateWebhooks() {
    var table = document.getElementById("show-webhook-table");
    if (!table)
        return;
    $("#show-webhook-table tbody tr").each(function () {
        var wh = $(this).data("webhook");
        var show = $(this).data("show");
        var triggers = [];
        $(this).find("input").each(function () {
            if ($(this).prop("checked"))
                triggers.push($(this).attr("name"));
        });
        var url = "/api/v1/shows/" + show + "/webhooks/" + wh;
        var method = "PUT";
        var data = { "triggers": triggers.join() };
        $.ajax({
            url: url,
            type: method,
            data: data,
            error: function (jqXHR, status, error) {
                console.error(status + ": " + error);
            }
        });
    });
}
function bufferShowEntryAddition(event) {
    event.preventDefault();
    var form = $(this).closest("form")[0];
    var data = new FormData(form);
    var show_id = parseInt(data.get("show_id"));
    var episode = parseInt(data.get("episode"));
    var magnet = data.get("magnet");
    var table = document.querySelector("#show-entry-table tbody");
    var episodes = [];
    for (var _i = 0, _a = Array.from(table.rows); _i < _a.length; _i++) {
        var row = _a[_i];
        var ep_cell = row.cells[0];
        var ep = parseInt(ep_cell.innerHTML);
        episodes.push(ep);
    }
    for (var _b = 0, entriesToAdd_2 = entriesToAdd; _b < entriesToAdd_2.length; _b++) {
        var entry_1 = entriesToAdd_2[_b];
        episodes.push(entry_1[1]);
    }
    if (episodes.includes(episode)) {
        $("#add-show-entry-form input[name='episode']").addClass("is-danger").effect("shake", { distance: 5, times: 2 }, 400);
        $("#add-show-entry-form p").removeClass("is-hidden");
        return;
    }
    $("#add-show-entry-form input[name='episode']").removeClass("is-danger");
    $("#add-show-entry-form p").addClass("is-hidden");
    entriesToAdd.push([show_id, episode, magnet]);
    var entry = {
        "id": 0,
        "show_id": show_id,
        "current_state": "buffered",
        "episode": episode
    };
    addRowToShowEntryTable(entry);
}
function sortedIndex(arr, val) {
    var low = 0;
    var high = arr.length;
    while (low < high) {
        var mid = (low + high) >>> 1;
        if (arr[mid] < val)
            low = mid + 1;
        else
            high = mid;
    }
    return low;
}
function addRowToShowEntryTable(entry) {
    var table = document.querySelector("#show-entry-table tbody");
    var episodes = [];
    for (var _i = 0, _a = Array.from(table.rows); _i < _a.length; _i++) {
        var row_1 = _a[_i];
        var ep_cell = row_1.cells[0];
        var ep = parseInt(ep_cell.innerHTML);
        episodes.push(ep);
    }
    var insertionIdx = sortedIndex(episodes, entry.episode);
    var row = table.insertRow(insertionIdx);
    var cell_episode = row.insertCell(0);
    var cell_status = row.insertCell(1);
    var cell_delete = row.insertCell(2);
    $(cell_episode).html(entry.episode.toString());
    $(cell_status).html(entry.current_state);
    var deleteBtn = document.createElement("button");
    $(deleteBtn).addClass("delete");
    $(deleteBtn).on("click", function () {
        if (entry.current_state !== "buffered")
            bufferShowEntryDeletion(entry.show_id, entry.id);
        entriesToAdd = entriesToAdd.filter(function (entryToAdd) {
            return entryToAdd[1] != entry.episode;
        });
        this.parentNode.parentNode.remove();
    });
    cell_delete.appendChild(deleteBtn);
}
function addRowToShowWebhookTable(webhook) {
    var table = document.querySelector("#show-webhook-table tbody");
    var row = table.insertRow(-1);
    $(row).addClass("has-text-centered");
    $(row).data("webhook", webhook.wh_id);
    $(row).data("show", webhook.show_id);
    var cell_basewh = row.insertCell(0);
    var cell_t_downloading = row.insertCell(1);
    var cell_t_downloaded = row.insertCell(2);
    var cell_t_renamed = row.insertCell(3);
    var cell_t_moved = row.insertCell(4);
    var cell_t_completed = row.insertCell(5);
    var cells = [cell_t_downloading, cell_t_downloaded, cell_t_renamed, cell_t_moved, cell_t_completed];
    for (var _i = 0, cells_1 = cells; _i < cells_1.length; _i++) {
        var cell = cells_1[_i];
        $(cell).addClass("is-vcentered");
        var checkbox = document.createElement("input");
        $(checkbox).attr("type", "checkbox").appendTo($(cell));
    }
    for (var _a = 0, all_triggers_1 = all_triggers; _a < all_triggers_1.length; _a++) {
        var trigger = all_triggers_1[_a];
        var input = $(eval("cell_t_" + trigger)).find("input");
        $(input).attr("name", trigger);
        if (webhook.triggers.includes(trigger))
            input.prop("checked", true);
    }
    var p = document.createElement("p");
    $(p).html(webhook.base.name);
    $(p).appendTo($(cell_basewh));
}
function bufferShowEntryDeletion(show_id, entry_id) {
    entriesToDelete.push([show_id, entry_id]);
}
function deleteShowEntry(show_id, entry_id) {
    var url = "/api/v1/shows/" + show_id + "/entries/" + entry_id;
    $.ajax({
        url: url,
        type: "DELETE"
    });
}
function addShowEntry(show_id, episode, magnet_url) {
    var url = "/api/v1/shows/" + show_id + "/entries";
    var payload = {
        episode: episode,
        magnet: magnet_url
    };
    $.ajax({
        url: url,
        type: "POST",
        data: $.param(payload),
        async: false
    });
}
function deleteShowCache(show_id) {
    var url = "/api/v1/shows/" + show_id + "/cache";
    $.ajax({
        url: url,
        type: "DELETE",
        success: function () {
            window.location.reload();
        }
    });
}
function displayShowInfo() {
    $("#edit-control-tabs ul li").removeClass("is-active");
    $("#show-info-tab").addClass("is-active");
    $("#edit-show-form").removeClass("is-hidden");
    $("#entry-tab-display").addClass("is-hidden");
    $("#webhook-tab-display").addClass("is-hidden");
}
function displayShowEntries() {
    $("#edit-control-tabs ul li").removeClass("is-active");
    $("#show-entry-tab").addClass("is-active");
    $("#edit-show-form").addClass("is-hidden");
    $("#entry-tab-display").removeClass("is-hidden");
    $("#webhook-tab-display").addClass("is-hidden");
}
function displayShowWebhooks() {
    $("#edit-control-tabs ul li").removeClass("is-active");
    $("#show-webhooks-tab").addClass("is-active");
    $("#edit-show-form").addClass("is-hidden");
    $("#entry-tab-display").addClass("is-hidden");
    $("#webhook-tab-display").removeClass("is-hidden");
}
function openAddShowModal() {
    var form = $("#add-show-form");
    form.trigger("reset");
    form.attr("action", "/api/v1/shows");
    form.attr("method", "POST");
    form.on("submit", submitAddOrEditShowForm);
    $(document.documentElement).addClass("is-clipped");
    $("#add-show-modal").addClass("is-active");
}
function openEditShowModal(show) {
    var form = $("#edit-show-form");
    var addEntryForm = $("#add-show-entry-form");
    var table = $("#show-entry-table tbody");
    var webhookTable = $("#show-webhook-table tbody");
    displayShowInfo();
    form.trigger("reset");
    addEntryForm.trigger("reset");
    $("#edit-show-form :input").each(function (i, elem) {
        $(elem).val(show[$(elem).attr("name")]);
    });
    $("#fix-match-input").val(show.kitsu_id);
    table.empty();
    webhookTable.empty();
    for (var _i = 0, _a = show.entries; _i < _a.length; _i++) {
        var entry = _a[_i];
        addRowToShowEntryTable(entry);
    }
    for (var _b = 0, _c = show.webhooks; _b < _c.length; _b++) {
        var webhook = _c[_b];
        addRowToShowWebhookTable(webhook);
    }
    $("#add-show-entry-form input[name='show_id']").val(show.id);
    form.attr("method", "PUT");
    form.attr("action", "/api/v1/shows/" + show.id);
    form.on("submit", submitAddOrEditShowForm);
    addEntryForm.on("submit", bufferShowEntryAddition);
    $("#del-cache-btn").on("click", function () {
        deleteShowCache(show.id);
    });
    $(document.documentElement).addClass("is-clipped");
    $("#edit-show-modal").addClass("is-active");
}
function openDeleteShowModal(show) {
    $("#delete-show-button").on("click", function (e) {
        e.preventDefault();
        $.ajax({
            url: "/api/v1/shows/" + show.id,
            type: "DELETE",
            success: function () {
                location.reload();
            }
        });
    });
    $("#item-to-delete-name").text(show.title);
    $(document.documentElement).addClass("is-clipped");
    $("#delete-show-modal").addClass("is-active");
}
function toggleFixMatchDropdown() {
    $("#fix-match-dropdown").toggleClass("is-active");
}
function closeModals() {
    if (modalsCanBeClosed) {
        entriesToDelete = [];
        entriesToAdd = [];
        $(".modal").removeClass("is-active");
        $("#add-show-entry-form input[name='episode']").removeClass("is-danger");
        $("#add-show-entry-form p").addClass("is-hidden");
        $(document.documentElement).removeClass("is-clipped");
    }
}
$(function () {
    $('.notification .delete').each(function () {
        $(this).on("click", function () {
            $(this).parent().remove();
        });
    });
    $("#fix-match-input").change(function () {
        $("input[name='kitsu_id']").val($(this).val());
    });
    $("#all-shows-link").on("click", function () {
        $(".column.is-hidden").removeClass("is-hidden");
        $("#back-to-top-link").removeClass("is-hidden");
        $(this).remove();
    });
    $("#back-to-top-link").on("click", function () {
        $("html, body").animate({ scrollTop: 0 }, "slow");
    });
});
