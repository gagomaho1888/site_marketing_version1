document.addEventListener("DOMContentLoaded", function () {
    var categoryField = document.getElementById("id_category");
    if (!categoryField) {
        return;
    }

    var rules = [
        { input: "id_shoe_size", categories: ["chaussure"] },
        { input: "id_clothing_sizes", categories: ["vetement du bas", "vetement du haut"] },
    ];

    var rows = {};
    document.querySelectorAll(".form-row").forEach(function (r) {
        rules.forEach(function (rule) {
            var fieldClass = "field-" + rule.input.replace(/^id_/, "");
            if (r.classList.contains(fieldClass)) {
                rows[rule.input] = r;
            }
        });
    });

    function normalize(value) {
        return (value || "").trim().toLowerCase();
    }

    function update() {
        var option = categoryField.options[categoryField.selectedIndex];
        var category = normalize(option ? option.textContent : "");
        rules.forEach(function (rule) {
            var row = rows[rule.input];
            if (!row) {
                return;
            }
            var show = rule.categories.indexOf(category) !== -1;
            row.style.display = show ? "" : "none";
            if (rule.input === "id_shoe_size") {
                document.getElementById("id_shoe_size").required = show;
            }
        });
    }

    categoryField.addEventListener("change", update);
    update();
});