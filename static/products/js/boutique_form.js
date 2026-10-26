document.addEventListener("DOMContentLoaded", function () {
    var categoryField = document.getElementById("id_category");
    var shoeBlock = document.getElementById("shoe-size-block");
    var clothingBlock = document.getElementById("clothing-size-block");

    if (!categoryField) {
        return;
    }

    function normalize(value) {
        return (value || "").trim().toLowerCase();
    }

    function kindFor(category) {
        if (category === "chaussure") {
            return "shoe";
        }
        if (category === "vetement du bas" || category === "vetement du haut") {
            return "clothing";
        }
        return null;
    }

    function update() {
        var option = categoryField.options[categoryField.selectedIndex];
        var category = normalize(option ? option.textContent : "");
        var kind = kindFor(category);
        if (shoeBlock) {
            shoeBlock.style.display = kind === "shoe" ? "" : "none";
        }
        if (clothingBlock) {
            clothingBlock.style.display = kind === "clothing" ? "" : "none";
        }
    }

    categoryField.addEventListener("change", update);
    update();
});
