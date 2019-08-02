var None = null;


function submitAddOrEditShowForm(event)
{

    event.preventDefault();
    var url = $(this).closest("form").attr("action");
    var method = $(this).closest("form").attr("method");
    var data = $(this).closest("form").serialize();
    $.ajax(
        {
            url: url,
            type: method,
            data: data,
            success: function(data) {
                location.reload();
            }
        }
    );
}


function addShowEntryFormSubmit(event)
{
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
            success: function(data) {
                var data = JSON.parse(data);
                var entry = data.entry;
                addRowToShowEntryTable(entry);
            }
        }
    );
}


function addRowToShowEntryTable(entry)
{
    var table = document.querySelector("#show-entry-table tbody"); 
    var row = table.insertRow(-1);

    var cell_episode = row.insertCell(0);
    var cell_status = row.insertCell(1);
    var cell_delete = row.insertCell(2);

    cell_episode.innerHTML = entry.episode;
    cell_status.innerHTML = entry.current_state;

    var deleteBtn = document.createElement("button");
    deleteBtn.classList.add("delete");
    deleteBtn.setAttribute(
        "onclick",
        `deleteShowEntry(${entry.show_id}, ${entry.id});this.parentNode.parentNode.remove();`
    );

    cell_delete.appendChild(deleteBtn);
}


function deleteShowEntry(show_id, entry_id)
{
    var url = "/api/shows/" + show_id + "/entries/" + entry_id;
    $.ajax(
        {
            url: url,
            type: "DELETE"
        }
    );
}


function displayShowInfo()
{
    var form = document.getElementById("edit-show-form");
    var table = document.getElementById("entry-tab-display");

    var infoTab = document.getElementById("show-info-tab");
    var entryTab = document.getElementById("show-entry-tab");

    infoTab.classList.add("is-active");
    entryTab.classList.remove("is-active");

    form.classList.remove("is-hidden");
    table.classList.add("is-hidden");
}


function displayShowEntries()
{
    var form = document.getElementById("edit-show-form");
    var table = document.getElementById("entry-tab-display");

    var infoTab = document.getElementById("show-info-tab");
    var entryTab = document.getElementById("show-entry-tab");

    infoTab.classList.remove("is-active");
    entryTab.classList.add("is-active");

    form.classList.add("is-hidden");
    table.classList.remove("is-hidden");
}


function openAddShowModal()
{
    var modal = document.getElementById("add-show-modal");
    var form = document.getElementById("add-show-form");

    form.reset();

    form.action = "/api/shows";
    form.method = "POST";
    form.onsubmit = submitAddOrEditShowForm;

    document.documentElement.classList.add("is-clipped");
    modal.classList.add("is-active");  
}


function openEditShowModal(show)
{
    var modal = document.getElementById("edit-show-modal");
    var form = document.getElementById("edit-show-form");

    var table = document.querySelector("#show-entry-table tbody");
    var tableCaption = document.getElementById("entry-table-caption");

    var addEntryForm = document.getElementById("add-show-entry-form");

    displayShowInfo();
    form.reset();
    addEntryForm.reset();

    inputs = form.getElementsByTagName("input");

    for (var i=0; i<inputs.length; i++)
    {
        inputs[i].value = show[inputs[i].name];
    }

    while (table.childNodes.length)
    {
        table.removeChild(table.childNodes[0]);
    }
    
    for (var i=0; i < show.entries.length; i++)
    {
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

    document.documentElement.classList.add("is-clipped");
    modal.classList.add("is-active");
}


function openDeleteShowModal(show)
{
    var modal = document.getElementById("delete-show-modal");
    var btn = document.getElementById("delete-show-button");

    btn.onclick = function(e) {
        e.preventDefault();
        $.ajax(
            {
                url: "/api/shows/" + show.id,
                type: "DELETE",
                success: function() {
                    location.reload();
                }
            }
        );
    }

    document.documentElement.classList.add("is-clipped");
    modal.classList.add("is-active");
}


function closeModals()
{
    modals = document.getElementsByClassName("modal");
    for (var i=0; i<modals.length; i++)
    {
        modals[i].classList.remove("is-active");
    }
    document.documentElement.classList.remove("is-clipped");
}