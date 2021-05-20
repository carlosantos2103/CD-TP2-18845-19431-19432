function httpGet()
{
    const http = new XMLHttpRequest();
    const url='http://127.0.0.1:5000/get_messages/5';
    http.open("GET", url);
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    var json = JSON.stringify({"username":"carlos"})
    http.send(json);

    http.onreadystatechange = (e) => {
        console.log(http.responseText)
    }
}

function httpDelete(message_id)
{
    const http = new XMLHttpRequest();
    const url='http://127.0.0.1:5000/remove_message/' + message_id;
    http.open("DELETE", url);
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    var json = JSON.stringify({"username":"carlos"})
    http.send(json);

    http.onreadystatechange = (e) => {
        console.log(http.responseText)
    }
}

function httpPost()
{
    const http = new XMLHttpRequest();
    const url='http://127.0.0.1:5000/send_messages';
    http.open("POST", url);
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    var json = JSON.stringify({"username":"ricardo", "receiver":"carlos", "message":"boas"})
    http.send(json);
    //http.send(JSON.stringify({'username':'ricardo'}));

    http.onreadystatechange = (e) => {
        console.log(http.responseText)
    }
}