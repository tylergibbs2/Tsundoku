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


function openEditShowModal(show)
{
    var modal = document.getElementById("edit-show-modal");
    var form = document.getElementById("edit-show-form");

    form.reset();

    inputs = form.getElementsByTagName("input");

    for (var i=0; i<inputs.length; i++)
    {
        inputs[i].value = show[inputs[i].name];
    }

    form.action = "/api/shows/" + show.id;
    form.onsubmit = submitForm;

    modal.classList.add("is-active");
}


function resetEditShowForm()
{
    var form = document.getElementById("edit-show-form");

    form.reset();
}


function closeModals()
{
    resetEditShowForm();

    modals = document.getElementsByClassName("modal");
    for (var i=0; i<modals.length; i++)
    {
        modals[i].classList.remove("is-active");
    }
}