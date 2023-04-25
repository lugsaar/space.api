document.addEventListener("DOMContentLoaded", function () {

    var spaceapi_uri = "https://lugsaar.github.io/space.api/api.json";
    var refresh_time = 60000;

    setInterval(function refresh_time() {

        fetch(spaceapi_uri).then(res => res.json()).then(data => {
          
            var openState = data.state.open;
            var buttonOpen = data.state.icon.open;
            var buttonClose = data.state.icon.closed;
            var lastchange = new Date((data.state.lastchange * 1000));
            document.querySelector('#spaceapi').innerHTML = "<img src='" + ((openState)?buttonOpen:buttonClose) + "'><span><b>Der Hackspace ist derzeit " + ((openState)?"geöffnet":"geschlossen") + "</b><br/>" + ((data.state.message)?data.state.message+"<br/>":"") + "<small>Letzte Statusänderung: " + lastchange.toLocaleString("de-DE") + "</small></span>";
        });

        return refresh_time;
    }(), refresh_time);

});