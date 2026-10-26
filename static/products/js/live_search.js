document.addEventListener("DOMContentLoaded", function () {
    var input = document.getElementById("live-search-input");
    if (!input) {
        return;
    }

    var panel = document.getElementById("live-search-results");
    var clearBtn = document.getElementById("live-search-clear");
    var form = input.closest("form");
    var submitBtn = input.closest("form").querySelector("[type=submit]");
    var currentCategory = (function () {
        var el = input.closest("form").querySelector("input[name=categorie]");
        return el ? el.value : "";
    })();
    var debounce;
    var controller = null;

    if (submitBtn) {
        submitBtn.style.display = "none";
    }

    function resetSearch() {
        clearTimeout(debounce);
        input.value = "";
        panel.classList.remove("show");
        panel.innerHTML = "";
        if (clearBtn) {
            clearBtn.classList.remove("visible");
        }
        input.focus();
    }

    function imageTag(p) {
        if (p.image) {
            return '<img src="' + p.image + '" alt="" loading="lazy">';
        }
        return '<div class="ls-thumb ls-thumb-empty"></div>';
    }

    function availability(p) {
        return p.available
            ? '<span class="ls-avail ls-in">Disponible</span>'
            : '<span class="ls-avail ls-out">Rupture</span>';
    }

    function render(results) {
        if (!results.length) {
            panel.innerHTML =
                '<div class="ls-empty">Aucun produit ne correspond à votre recherche.</div>';
            panel.classList.add("show");
            return;
        }
        var html = results
            .map(function (p) {
                return (
                    '<a class="ls-item" href="' +
                    p.url +
                    '">' +
                    '<div class="ls-thumb">' +
                    imageTag(p) +
                    "</div>" +
                    '<div class="ls-body">' +
                    '<div class="ls-name">' +
                    p.name +
                    "</div>" +
                    '<div class="ls-cat">' +
                    (p.category || "") +
                    "</div>" +
                    '<div class="ls-meta"><span class="ls-price">' +
                    p.price +
                    " FCFA</span>" +
                    availability(p) +
                    "</div>" +
                    "</div>" +
                    "</a>"
                );
            })
            .join("");
        panel.innerHTML = html;
        panel.classList.add("show");
    }

    function doSearch(query) {
        if (controller) {
            controller.abort();
        }
        controller = new AbortController();
        var params = new URLSearchParams({ q: query });
        if (currentCategory) {
            params.set("categorie", currentCategory);
        }
        fetch("/produits/recherche/?" + params.toString(), {
            signal: controller.signal,
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then(function (r) {
                return r.json();
            })
            .then(function (data) {
                render(data.results);
            })
            .catch(function () {
                /* ignore aborted/errors */
            });
    }

    input.addEventListener("input", function () {
        var query = input.value.trim();
        if (clearBtn) {
            clearBtn.classList.toggle("visible", query.length > 0);
        }
        if (!query) {
            clearTimeout(debounce);
            panel.classList.remove("show");
            panel.innerHTML = "";
            return;
        }
        clearTimeout(debounce);
        debounce = setTimeout(function () {
            doSearch(query);
        }, 250);
    });

    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            resetSearch();
        });
    }

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            panel.classList.remove("show");
        }
    });

    document.addEventListener("click", function (e) {
        if (!panel.contains(e.target) && e.target !== input) {
            panel.classList.remove("show");
        }
    });

    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            var query = input.value.trim();
            if (query) {
                doSearch(query);
            }
        });
    }
});
