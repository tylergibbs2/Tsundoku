var entriesToDelete: number[][] = [];
var entriesToAdd: any[] = [];

var all_triggers: string[] = ["downloading", "downloaded", "renamed", "moved", "completed"];

var modalsCanBeClosed: boolean = true;


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
    };

    setTimeout(poll, 5000);
}


function submitAddOrEditShowForm(event: Event) {
    showAddorEditProgressBars();

    event.preventDefault();
    let url = $(this).closest("form").attr("action");
    let method = $(this).closest("form").attr("method");
    let data = $(this).closest("form").serialize();

    updateWebhooks();

    // delete all buffered deletions
    for (const entry of entriesToDelete) {
        // entry[0] is show_id, entry[1] is entry_id
        deleteShowEntry(entry[0], entry[1]);
    }
    for (const entry of entriesToAdd) {
        /*
        entry[0] is show_id
        entry[1] is episode
        entry[2] is magnet
        */
       addShowEntry(entry[0], entry[1], entry[2]);
    }

    $.ajax(
        {
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
        }
    );
}


function updateWebhooks() {
    let table: HTMLElement = document.getElementById("show-webhook-table");
    if (!table)
        return;

    $("#show-webhook-table tbody tr").each(function() {
        let wh: string = $(this).data("webhook");
        let show: string = $(this).data("show");
        let triggers: string[] = [];
        $(this).find("input").each(function() {
            if ($(this).prop("checked"))
                triggers.push($(this).attr("name"));
        });

        let url: string = `/api/shows/${show}/webhooks/${wh}`;
        let method: string = "PUT";
        let data: object = { "triggers": triggers.join() };

        $.ajax(
            {
                url: url,
                type: method,
                data: data,
                error: function (jqXHR, status, error) {
                    console.error(`${status}: ${error}`);
                }
            }
        );
    });

}


function bufferShowEntryAddition(event: Event) {
    event.preventDefault();

    let form: HTMLFormElement = $(this).closest("form")[0];
    let data = new FormData(form);

    let show_id = parseInt(data.get("show_id") as string);
    let episode = parseInt(data.get("episode") as string);
    let magnet = data.get("magnet");

    let table: HTMLTableElement = document.querySelector("#show-entry-table tbody");
    let episodes: number[] = [];
    for (const row of Array.from(table.rows)) {
        let ep_cell: HTMLTableCellElement = row.cells[0];
        let ep: number = parseInt(ep_cell.innerHTML);
        episodes.push(ep);
    }
    for (const entry of entriesToAdd)
        episodes.push(entry[1]);

    if (episodes.includes(episode)) {
        $("#add-show-entry-form input[name='episode']").addClass("is-danger").effect("shake", {distance: 5, times: 2}, 400);
        $("#add-show-entry-form p").removeClass("is-hidden");
        return;
    }

    $("#add-show-entry-form input[name='episode']").removeClass("is-danger");
    $("#add-show-entry-form p").addClass("is-hidden");

    entriesToAdd.push([show_id, episode, magnet])

    let entry = {
        "id": 0,
        "show_id": show_id,
        "current_state": "buffered",
        "episode": episode
    }
    addRowToShowEntryTable(entry);
}


function sortedIndex(arr: number[], val: number): number {
    let low = 0;
    let high = arr.length;

    while (low < high) {
        let mid = (low + high) >>> 1;
        if (arr[mid] < val)
            low = mid + 1;
        else
            high = mid;
    }

    return low;
}


function addRowToShowEntryTable(entry: PartialEntry) {
    let table: HTMLTableElement = document.querySelector("#show-entry-table tbody");

    let episodes: number[] = [];
    for (const row of Array.from(table.rows)) {
        let ep_cell: HTMLTableCellElement = row.cells[0];
        let ep: number = parseInt(ep_cell.innerHTML);
        episodes.push(ep);
    }

    let insertionIdx: number = sortedIndex(episodes, entry.episode);
    let row: HTMLTableRowElement = table.insertRow(insertionIdx);

    let cell_episode: HTMLTableCellElement = row.insertCell(0);
    let cell_status: HTMLTableCellElement = row.insertCell(1);
    let cell_delete: HTMLTableCellElement = row.insertCell(2);

    $(cell_episode).html(entry.episode.toString());
    $(cell_status).html(entry.current_state);

    let deleteBtn: HTMLButtonElement = document.createElement("button");
    $(deleteBtn).addClass("delete");

    $(deleteBtn).on("click", function () {
        if (entry.current_state !== "buffered")
            bufferShowEntryDeletion(entry.show_id, entry.id);
        entriesToAdd = entriesToAdd.filter( function(entryToAdd) {
            return entryToAdd[1] != entry.episode;
        });

        (this.parentNode.parentNode as any).remove();
    })

    cell_delete.appendChild(deleteBtn);
}


function addRowToShowWebhookTable(webhook: Webhook) {
    let table: HTMLTableElement = document.querySelector("#show-webhook-table tbody");

    let row = table.insertRow(-1);
    $(row).addClass("has-text-centered");
    $(row).data("webhook", webhook.wh_id);
    $(row).data("show", webhook.show_id);

    let cell_basewh: HTMLTableCellElement = row.insertCell(0);
    let cell_t_downloading: HTMLTableCellElement = row.insertCell(1);
    let cell_t_downloaded: HTMLTableCellElement = row.insertCell(2);
    let cell_t_renamed: HTMLTableCellElement = row.insertCell(3);
    let cell_t_moved: HTMLTableCellElement = row.insertCell(4);
    let cell_t_completed: HTMLTableCellElement = row.insertCell(5);

    let cells: HTMLTableCellElement[] = [cell_t_downloading, cell_t_downloaded, cell_t_renamed, cell_t_moved, cell_t_completed];
    for (const cell of cells) {
        $(cell).addClass("is-vcentered");
        let checkbox = document.createElement("input");
        $(checkbox).attr("type", "checkbox").appendTo( $(cell) );
    }

    for (const trigger of all_triggers) {
        let input = $(eval(`cell_t_${trigger}`)).find("input");
        $(input).attr("name", trigger);
        if (webhook.triggers.includes(trigger))
            input.prop("checked", true);
    }

    let p: HTMLParagraphElement = document.createElement("p");
    $(p).html(webhook.base.name);
    $(p).appendTo( $(cell_basewh) );
}


function bufferShowEntryDeletion(show_id: number, entry_id: number) {
    entriesToDelete.push([show_id, entry_id]);
}


function deleteShowEntry(show_id: number, entry_id: number) {
    let url: string = `/api/shows/${show_id}/entries/${entry_id}`;
    $.ajax({
        url: url,
        type: "DELETE"
    });
}


function addShowEntry(show_id: number, episode: number, magnet_url: string) {
    let url: string = `/api/shows/${show_id}/entries`;
    let payload: object = {
        episode: episode,
        magnet: magnet_url
    }
    $.ajax({
        url: url,
        type: "POST",
        data: $.param(payload),
        async: false
    });
}

function deleteShowCache(show_id: number) {
    let url = `/api/shows/${show_id}/cache`;
    $.ajax(
        {
            url: url,
            type: "DELETE",
            success: function () {
                window.location.reload();
            }
        }
    );
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
    let form: JQuery = $("#add-show-form");

    form.trigger("reset");

    form.attr("action", "/api/shows");
    form.attr("method", "POST");
    form.on("submit", submitAddOrEditShowForm);

    $(document.documentElement).addClass("is-clipped");
    $("#add-show-modal").addClass("is-active");
}


function openEditShowModal(show: Show) {
    let form: JQuery = $("#edit-show-form");
    let addEntryForm: JQuery = $("#add-show-entry-form");

    let table: JQuery = $("#show-entry-table tbody");
    let webhookTable: JQuery = $("#show-webhook-table tbody");

    displayShowInfo();
    form.trigger("reset");
    addEntryForm.trigger("reset");

    $("#edit-show-form :input").each(function (i, elem) {
        $(elem).val(show[$(elem).attr("name")])
    });

    $("#fix-match-input").val(show.kitsu_id);

    table.empty();
    webhookTable.empty();

    for (const entry of show.entries) {
        addRowToShowEntryTable(entry);
    }

    for (const webhook of show.webhooks) {
        addRowToShowWebhookTable(webhook);
    }

    $("#add-show-entry-form input[name='show_id']").val(show.id);

    form.attr("method", "PUT");
    form.attr("action", `/api/shows/${show.id}`);

    form.on("submit", submitAddOrEditShowForm);

    addEntryForm.on("submit", bufferShowEntryAddition);

    $("#del-cache-btn").on("click", function () {
        deleteShowCache(show.id);
    })

    $(document.documentElement).addClass("is-clipped");
    $("#edit-show-modal").addClass("is-active");
}


function openDeleteShowModal(show: Show) {
    $("#delete-show-button").on("click", function (e) {
        e.preventDefault();
        $.ajax(
            {
                url: `/api/shows/${show.id}`,
                type: "DELETE",
                success: function () {
                    location.reload();
                }
            }
        );
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
        })
    });

    $("#fix-match-input").change(function () {
        $("input[name='kitsu_id']").val($(this).val());
    });

    $("#all-shows-link").on("click", function () {
        $(".column.is-hidden").removeClass("is-hidden");
        $("#back-to-top-link").removeClass("is-hidden");
        $(this).remove();
    })

    $("#back-to-top-link").on("click", function() {
        $("html, body").animate({ scrollTop: 0 }, "slow");
    });
});