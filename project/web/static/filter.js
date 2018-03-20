function filter() {
    var inputDir, inputFile, filterDir, filterFile, found, element, tag, i;

    inputDir = document.getElementById("filterTextDirectory");
    inputFile = document.getElementById("filterTextFile");
    filterDir = inputDir.value.replace(/'/g, "").toUpperCase();
    filterFile = inputFile.value.replace(/'/g, "").toUpperCase();

    element = document.getElementById("filterable");
    tag = element.getElementsByTagName("tr");

    for (i = 0; i < tag.length; i++) {
        if (tag[i].id == "directory-container") {
            if (tag[i].innerHTML.replace(/'/g, "").toUpperCase().indexOf(filterDir) > -1) {
                found = true;
            }
        }
        if (tag[i].id == "file-container") {
            if (tag[i].innerHTML.replace(/'/g, "").toUpperCase().indexOf(filterFile) > -1) {
                found = true;
            }
        }

        if (found) {
            tag[i].style.display = "";
            found = false;
        } else {
            tag[i].style.display = "none";
        }
    }
}
