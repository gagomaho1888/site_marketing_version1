console.log("Boutique en ligne — script chargé");

document.addEventListener("DOMContentLoaded", function () {
    var toggler = document.querySelector(".nav-toggler");
    var links = document.querySelector(".nav-links");
    if (!toggler || !links) {
        return;
    }

    toggler.addEventListener("click", function () {
        var isOpen = links.classList.toggle("open");
        toggler.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    links.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            links.classList.remove("open");
            toggler.setAttribute("aria-expanded", "false");
        });
    });
});