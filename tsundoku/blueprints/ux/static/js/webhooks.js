var None = null;

function submitAddWebhookForm(event) {
    event.preventDefault();
    let url = $(this).closest("form").attr("action");
    let method = $(this).closest("form").attr("method");
    let data = $(this).closest("form").serialize();

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


$(document).ready(function () {
    $('.notification .delete').each(function () {
        $(this).on("click", function () {
            $(this).parent().remove();
        })
    });
});