function onActionClicked(event) {
    let WAIT = "wait-for-confirmation";
    let actionLink = event.target;

    if(actionLink.classList.contains(WAIT)) {
        // The action link has been already clicked, this click is the final confirm
        return true;
    } else {
        actionLink.classList.add(WAIT);
        actionLink.textContent = actionLink.textContent.trim()+" bestätigen"
        return false;
    }
}

function addAccidentalClickPreventionListener() {
    for(action of document.getElementsByClassName("action")) {
        if(action.tagName == "A" && action.classList.contains("needs-confirmation")) {
            action.onclick = onActionClicked;
        }
    }
}

document.addEventListener("DOMContentLoaded", addAccidentalClickPreventionListener);
