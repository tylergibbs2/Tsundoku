import {} from "../patch";
import { WebhookBase } from "../interfaces";

function submitAddWebhookForm(event: Event) {
    event.preventDefault();
    let url: string = $(this).closest("form").attr("action");
    let method: string = $(this).closest("form").attr("method");
    let data: string = $(this).closest("form").serialize();

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


function openAddWebhookModal() {
    let form: JQuery = $("#add-webhook-form");

    form.attr("action", "/api/v1/webhooks");
    form.attr("method", "POST");
    form.on("submit", submitAddWebhookForm);

    $(document.documentElement).addClass("is-clipped");
    $("#add-webhook-modal").addClass("is-active");
};


function openEditWebhookModal(webhook: WebhookBase) {
    let form: JQuery = $("#edit-webhook-form");
    form.trigger("reset");

    $("#edit-webhook-form :input").each(function (i: number, elem: HTMLElement) {
        let name: string = $(elem).attr("name");
        $(elem).val(webhook.name)
    });

    form.attr("method", "PUT");
    form.attr("action", `/api/v1/webhooks/${webhook.base_id}`);

    form.on("submit", submitAddWebhookForm);

    $(document.documentElement).addClass("is-clipped");
    $("#edit-webhook-modal").addClass("is-active");
}


function openDeleteWebhookModal(webhook: WebhookBase) {
    $("#delete-webhook-button").on("click", function (e) {
        e.preventDefault();
        $.ajax(
            {
                url: `/api/v1/webhooks/${webhook.base_id}`,
                type: "DELETE",
                success: function () {
                    location.reload();
                }
            }
        );
    });
    $("#item-to-delete-name").text(webhook.name);

    $(document.documentElement).addClass("is-clipped");
    $("#delete-webhook-modal").addClass("is-active");
}


function closeWebhookModals() {
    $(".modal").removeClass("is-active");
    $(document.documentElement).removeClass("is-clipped");
}


$(function () {
    $('.notification .delete').each(function () {
        $(this).on("click", function () {
            $(this).parent().remove();
        })
    });
});

// PATCHES
window.openAddWebhookModal = openAddWebhookModal;
window.openEditWebhookModal = openEditWebhookModal;
window.openDeleteWebhookModal = openDeleteWebhookModal;
window.closeWebhookModals = closeWebhookModals;