function launchModal() {
    let modal = document.getElementById("help-modal");

    modal.classList.add("is-active");
    document.documentElement.classList.add("is-clipped");
}

function closeModal() {
    let modal = document.getElementById("help-modal");

    modal.classList.remove("is-active");
    document.documentElement.classList.remove("is-clipped");
}