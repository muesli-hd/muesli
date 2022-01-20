let backgroundColorInterval;

function getRandomColor() {
    let letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function setRandomBackgroundColor(waitTime) {
    $(".navbar").removeClass('navbar-dark bg-dark').addClass('navbar-light').css('background-color', getRandomColor());
    backgroundColorInterval = setInterval(function() {
        $(".navbar").css('background-color', getRandomColor());
    }, waitTime);
}

function aprilFool() {
    let waitTime = 4000;
    let now = new Date();
    if (now.getDate() === 1 && now.getMonth() === 3) {
        setRandomBackgroundColor(waitTime);
    }
}
