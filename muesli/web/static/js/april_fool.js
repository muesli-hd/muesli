var backgroundColorInterval;

function getRandomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function setRandomBackgroundColor(waitTime) {
    document.getElementById("header").style.backgroundColor = getRandomColor();
    backgroundColorInterval = setInterval(function() {
        document.getElementById("header").style.backgroundColor = getRandomColor();
    }, waitTime);
}

function aprilFool() {
    var waitTime = 10000;
    var now = new Date();
    if (now.getDate() === 1 && now.getMonth() === 3) {
        setRandomBackgroundColor(waitTime);
    }
}
