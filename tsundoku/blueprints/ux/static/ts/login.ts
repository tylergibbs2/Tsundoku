function launchModal() {
    let modal: HTMLElement = document.getElementById("help-modal");

    modal.classList.add("is-active");
    document.documentElement.classList.add("is-clipped");
}

function closeModal() {
    let modal: HTMLElement = document.getElementById("help-modal");

    modal.classList.remove("is-active");
    document.documentElement.classList.remove("is-clipped");
}