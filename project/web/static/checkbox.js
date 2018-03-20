function isHidden(o) {
    return(o.offsetParent === null)
}

function checkMatches(parent) {
    var checkbox, i;

    // Get all checkboxes with the same name as their parent.
    checkbox = document.getElementsByName(parent.name)

    for (i = 0; i < checkbox.length; i++) {
        if (isHidden(checkbox[i])) {
            // If checkbox is hidden and we touch the parent's checkbox, uncheck the hidden child.
            checkbox[i].checked = false;
        } else {
            // If checkbox is visible and we touch the parent's checkbox, match whatever the parent's checkbox state $
            checkbox[i].checked = parent.checked;
        }
    }
}

function checkAllVisible(bool) {
    var check, element, input, i;

    if (bool) {
        check = true;
    } else {
        check = false;
    }

    element = document.getElementById("filterable");
    input = element.getElementsByTagName("input");

    for (i = 0; i < input.length; i++) {
        if (input[i].getAttribute("type") == "checkbox") {
            if (input[i].id == "file") {
                if (isHidden(input[i])) {
                    // do nothing
                } else {
                    input[i].checked = check;
                }
            }
        }
    }
}
