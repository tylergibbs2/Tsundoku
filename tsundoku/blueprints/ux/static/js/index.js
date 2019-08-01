var None = null;


function submitForm(event)
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
            success: function() {
                location.reload();
            }
        }
    );
}


function deleteShowEntry(show_id, entry_id)
{
    var url = "/api/shows/" + show_id + "/entries/" + entry_id;
    $.ajax(
        {
            url: url,
            type: "DELETE",
            success: function() {

            }
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
    form.onsubmit = submitForm;

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
        var row = table.insertRow(i);

        var cell_id = row.insertCell(0);
        var cell_episode = row.insertCell(1);
        var cell_status = row.insertCell(2);
        var cell_delete = row.insertCell(3);

        cell_id.innerHTML = show.entries[i].id;
        cell_episode.innerHTML = show.entries[i].episode;
        cell_status.innerHTML = show.entries[i].current_state;

        var deleteBtn = document.createElement("button");
        deleteBtn.classList.add("delete");
        deleteBtn.setAttribute(
            "onclick",
            `deleteShowEntry(${show.id}, ${show.entries[i].id});this.parentNode.parentNode.remove();`
        );

        cell_delete.appendChild(deleteBtn);
    }

    tableCaption.innerHTML = show.title;

    form.action = `/api/shows/${show.id}`;
    form.method = "PUT";
    form.onsubmit = submitForm;

    addEntryForm.action = `/api/shows/${show.id}/entries`;
    addEntryForm.method = "POST";
    addEntryForm.onsubmit = submitForm;

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