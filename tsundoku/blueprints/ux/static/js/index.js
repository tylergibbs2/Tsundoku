var None = null;


function submitAddOrEditShowForm(event) {
    event.preventDefault();
    var url = $(this).closest("form").attr("action");
    var method = $(this).closest("form").attr("method");
    var data = $(this).closest("form").serialize();
    $.ajax(
        {
            url: url,
            type: method,
            data: data,
            success: function (data) {
                location.reload();
            },
            error: function (jqXHR, status, error) {
                alert("There was an error processing the request.");
            }
        }
    );
}


function addShowEntryFormSubmit(event) {
    event.preventDefault();

    var form = $(this).closest("form");
    var url = form.attr("action");
    var method = form.attr("method");
    var data = form.serialize();
    $.ajax(
        {
            url: url,
            type: method,
            data: data,
            success: function (data) {
                var data = JSON.parse(data);
                var entry = data.entry;
                addRowToShowEntryTable(entry);
            },
            error: function (jqXHR, status, error) {
                alert("There was an error processing the request.");
            }
        }
    );
}


function addRowToShowEntryTable(entry) {
    let table = document.querySelector("#show-entry-table tbody");
    let row = table.insertRow(-1);

    let cell_episode = row.insertCell(0);
    let cell_status = row.insertCell(1);
    let cell_delete = row.insertCell(2);

    cell_episode.innerHTML = entry.episode;
    cell_status.innerHTML = entry.current_state;

    var deleteBtn = document.createElement("button");
    deleteBtn.classList.add("delete");
    deleteBtn.onclick = function() {
        deleteShowEntry(entry.show_id, entry.id);
        this.parentNode.parentNode.remove();
    }

    cell_delete.appendChild(deleteBtn);
}


function deleteShowEntry(show_id, entry_id) {
    var url = `/api/shows/${show_id}/entries/${entry_id}`;
    $.ajax(
        {
            url: url,
            type: "DELETE"
        }
    );
}


function deleteShowCache(show_id) {
    var url = `/api/shows/${show_id}/cache`;
    $.ajax(
        {
            url: url,
            type: "DELETE",
            success: function() {
                window.location.reload();
            }
        }
    );
}


function displayShowInfo() {
    $("#show-info-tab").addClass("is-active");
    $("#show-entry-tab").removeClass("is-active");

    $("#edit-show-form").removeClass("is-hidden");
    $("#entry-tab-display").addClass("is-hidden");
}


function displayShowEntries() {
    $("#show-info-tab").removeClass("is-active");
    $("#show-entry-tab").addClass("is-active");

    $("#edit-show-form").addClass("is-hidden");
    $("#entry-tab-display").removeClass("is-hidden");
}


function openAddShowModal() {
    let form = document.getElementById("add-show-form");

    form.reset();

    form.action = "/api/shows";
    form.method = "POST";
    form.onsubmit = submitAddOrEditShowForm;

    $(document.documentElement).addClass("is-clipped");
    $("#add-show-modal").addClass("is-active");
}


function openEditShowModal(show) {
    let form = document.getElementById("edit-show-form");

    let table = document.querySelector("#show-entry-table tbody");
    let tableCaption = document.getElementById("entry-table-caption");

    let addEntryForm = document.getElementById("add-show-entry-form");
    let delCacheBtn = document.getElementById("del-cache-btn");

    displayShowInfo();
    form.reset();
    addEntryForm.reset();

    inputs = form.getElementsByTagName("input");

    for (let i = 0; i < inputs.length; i++) {
        inputs[i].value = show[inputs[i].name];
    }

    while (table.childNodes.length) {
        table.removeChild(table.childNodes[0]);
    }

    for (let i = 0; i < show.entries.length; i++) {
        var entry = show.entries[i];
        addRowToShowEntryTable(entry);
    }

    tableCaption.innerHTML = show.title;

    form.action = `/api/shows/${show.id}`;
    form.method = "PUT";
    form.onsubmit = submitAddOrEditShowForm;

    addEntryForm.action = `/api/shows/${show.id}/entries`;
    addEntryForm.method = "POST";
    addEntryForm.onsubmit = addShowEntryFormSubmit;

    delCacheBtn.onclick = function () {
        deleteShowCache(show.id);
    }

    $(document.documentElement).addClass("is-clipped");
    $("#edit-show-modal").addClass("is-active");
}


function openDeleteShowModal(show) {
    let btn = document.getElementById("delete-show-button");

    btn.onclick = function (e) {
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
    }

    $(document.documentElement).addClass("is-clipped");
    $("#delete-show-modal").addClass("is-active");
}


function closeModals() {
    $(".modal").removeClass("is-active");
    $(document.documentElement).removeClass("is-clipped");
}


$(document).ready(function() {
    $('.notification .delete').each(function () {
        $(this).on("click", function () {
            $(this).parent().remove();
        })
    });
});