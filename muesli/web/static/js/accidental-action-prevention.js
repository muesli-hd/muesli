function accidentalClickPrevention(event) {
    let WAIT = "wait-for-confirmation";
    let actionLink = event.target; 
    console.log(actionLink);

    if(actionLink.classList.contains(WAIT)) {
        // The action link has been already clicked, this click is the final confirm
        return true;
    } else {
        actionLink.classList.add(WAIT);
        actionLink.textContent = actionLink.textContent.trim()+" bestätigen"
        return false;
    }
}

