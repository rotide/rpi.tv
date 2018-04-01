function filter(iParent, iChild, tParent, tChild) {
    var inputParent, inputChild, filterParent, filterChild, found, tags, type, i;

    inputParent = document.getElementById(iParent);
    inputChild = document.getElementById(iChild);
    filterParent = inputParent.value.replace(/'/g, "").toUpperCase();
    filterChild = inputChild.value.replace(/'/g, "").toUpperCase();

    // Get all DIV tags.
    tags = document.getElementsByTagName("div");

    for (i = 0; i < tags.length; i++) {
        // Get TYPE data from tag (HTML: data-type attribute).
        type = tags[i].dataset.type;

        // If TYPE is defined as tParent or tChild, continue.
        if (type == tParent || type == tChild) {
            found = false;

            if (type == tParent) {
                if (tags[i].dataset.parent.replace(/'/g, "").toUpperCase().indexOf(filterParent) > -1) {
                    found = true;
                }
            } else if (type == tChild) {
                if (tags[i].dataset.child.replace(/'/g, "").toUpperCase().indexOf(filterChild) > -1) {
                    found = true;
                }
            }

            if (found) {
                tags[i].style.display = "";
            } else {
                tags[i].style.display = "none";
            }
        }
    }
}
