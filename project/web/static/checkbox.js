function isHidden(o) {
    return(o.offsetParent === null)
}

function checkMatches(parent) {
    var checkboxes, children, i;

    children = document.querySelectorAll("[data-family='checkbox-child']");

    checkboxes = [];
    for (i = 0; i < children.length; i++) {
        if (children[i].dataset.directory == parent.dataset.directory) {
            checkboxes.push(children[i]);
        }
    }

    for (i = 0; i < checkboxes.length; i++) {
        if (isHidden(checkboxes[i])) {
            // If checkbox is hidden and we touch the parent's checkbox, uncheck the hidden child.
            checkboxes[i].checked = false;
        } else {
            // If checkbox is visible and we touch the parent's checkbox, match whatever the parent's checkbox state is.
            checkboxes[i].checked = parent.checked;
        }
    }
}

function checkAllVisible(bool) {
    var check, children, i;

    if (bool) {
        check = true;
    } else {
        check = false;
    }

    children = document.querySelectorAll("[data-family='checkbox-child']");

    for (i = 0; i < children.length; i++) {
        if (isHidden(children[i])) {
            // do nothing
        } else {
            children[i].checked = check;
        }
    }
}