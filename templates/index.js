var username
var password

function SendHTTPRequest()
{
    const http = new XMLHttpRequest();
    const url = "http://127.0.0.1:5000/" + $("#domain").val();
    const method = $("#method").val();
    const json = $("#json").val();

    http.open(method, url);
    http.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    http.send(json);

    http.onreadystatechange = (e) => {
        $("#message").text(http.status)
    }
}


function TryLogin()
{
    const http = new XMLHttpRequest();
    const url = "http://127.0.0.1:5000/login";
    const method = "GET"
    const json = {};
    username = $("#username").val();
    password = $("#password").val();
    
    http.open(method, url);
    http.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    http.send(json);

    http.onreadystatechange = (e) => {
        if (http.readyState === 4)
            document.write(http.response)
    }
}


$(document).ready(function(){
    var socket = io.connect('http://127.0.0.1:5000/');
    console.log(socket)
    // Update the counter when a new user connects
    socket.on('users', function(users) {
        console.log(socket)
        userCount = document.getElementById('user_counter');
        console.log(userCount)
    });
});