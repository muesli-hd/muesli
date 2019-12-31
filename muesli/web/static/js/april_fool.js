var backgroundColorInterval, cursorInterval;

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

function changeCursor(waitTime) {
    var cursors = [
        'url(https://www.mathi.uni-heidelberg.de/~jvisintini/aprilfool/mathematikon_32.png), auto',
        'url(https://www.mathi.uni-heidelberg.de/~jvisintini/aprilfool/unihd_32.png), auto',
        'url(https://www.mathi.uni-heidelberg.de/~jvisintini/aprilfool/physik_32.png), auto',
        'url(https://www.mathi.uni-heidelberg.de/~jvisintini/aprilfool/websurface_32.png), auto',
        'url(https://www.mathi.uni-heidelberg.de/~jvisintini/aprilfool/kleinbottle_32.png), auto',
        'url(https://www.mathi.uni-heidelberg.de/~jvisintini/aprilfool/moebiusstrip_32.png), auto',
    ];
    document.body.style.cursor = cursors[cursors.length-1];
    var cursorIdx = 0;
    cursorInterval = setInterval(function() {
        document.body.style.cursor = cursors[cursorIdx];
        cursorIdx = (cursorIdx + 1) % cursors.length;
    }, waitTime);
}

function aprilFool() {
    var waitTime = 10000;
    var now = new Date();
    if (now.getDate() === 1 && now.getMonth() === 3) {
        changeCursor(waitTime);
        setRandomBackgroundColor(waitTime);
    }
}
