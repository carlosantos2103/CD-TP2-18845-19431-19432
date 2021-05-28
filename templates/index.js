var username
var password

function SendHTTPRequest()
{
    const http = new XMLHttpRequest();
    const url = "http://127.0.0.1:5000/" + document.getElementById("domain").value;
    const method = document.getElementById("method").value;
    const json = document.getElementById("json").value

    http.open(method, url);
    http.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    req.responseType = "document";
    http.send(JSON.stringify(json));
        
    http.onreadystatechange = (e) => {
        if (http.readyState === 4){
            document.getElementById("message").text = http.responseText
            console.log("|" + http.responseType + "|")
            var element = document.createElement('a');
            element.setAttribute('href', 'data:attachment;charset=utf-8,' + encodeURIComponent(http.responseText));
            element.setAttribute('download', "filename");
    
            element.style.display = 'none';
            document.body.appendChild(element);
    
            element.click();
    
            document.body.removeChild(element);
        }
    }
}


function TryLogin()
{
    socketsStart()

    const http = new XMLHttpRequest();
    const url = "http://127.0.0.1:5000/login";
    const method = "GET"
    const json = {};
    username = document.getElementById("username").value;
    password = document.getElementById("password").value;
    
    http.open(method, url);
    http.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    http.send(json);

    http.onreadystatechange = (e) => {
        if (http.readyState === 4)
            document.write(http.response)
    }
}

function AddUser()
{
    const http = new XMLHttpRequest();
    const url = "http://127.0.0.1:5000/users/create_account";
    const method = "POST"
    username = document.getElementById("username").value;
    password = document.getElementById("password").value;
    const json = {"username":username, "password":password};

    http.open(method, url);
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

    http.send(JSON.stringify(json));

    http.onreadystatechange = (e) => {
        if (http.readyState === 4)
            document.write(http.response)
    }
}

function SendHTTPRequestFile()
{
    const http = new XMLHttpRequest();
    const url = "http://127.0.0.1:5000/" + document.getElementById("domain").value;
    const method = document.getElementById("method").value;
    const json = document.getElementById("json").value

    http.open(method, url, true);
    http.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
    const file = document.getElementById("file")[0].files[0]
    console.log("o ficheiro")
    console.log(file)
    
    var formData = new FormData();
    formData.append("file", file);
    http.send(formData);
        
    http.onreadystatechange = (e) => {
        document.getElementById("message").text = http.responseText
    }
}

function socketsStart(){
    var socket = io();
    console.log(socket)
    socket.on('connect', function(data) {
        socket.emit('event', {data:"ola"})
    });
    /*socket.on('new room message', function(data) {
        console.log(data)
    });*/
};