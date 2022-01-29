import {
    WidgetInstance
} from "friendly-challenge";
window.addEventListener("DOMContentLoaded", function () {
    // ...

    var doneCallback, element, options, widget;

    doneCallback = function (solution) {
        //console.log(solution);
        document.querySelector("#form-submit-button").disabled = false;
    };
    const errorCallback = (err) => {
        console.log('There was an error when trying to solve the Captcha.');
        console.log(err);
    }
    element = document.querySelector('#captcha-widget');
    if (element != null) {
        options = {
            doneCallback: doneCallback,
            errorCallback,
            puzzleEndpoint: document.querySelector('#captcha-widget').dataset.puzzle_url,
            startMode: "auto"
        };

        widget = new WidgetInstance(element, options);
        //DO not uncomment, evil
        //    widget.reset();
    }
}, false)
