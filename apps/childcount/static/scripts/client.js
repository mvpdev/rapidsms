
/* Data Entry HTTP Client */

proxy_url = '/dataentry/proxypost';

/*
 * proxy_send - sends a message to DataEntry Backend
 * message_obj must contain: identity and message
 */ 
function proxy_send(message_obj, callback)
{
    var proxy_answer = {};
    $.ajax({
        type: 'POST',
        url: proxy_url,
        data: message_obj,
        dataType: 'json',
        success: callback
    });
    return proxy_answer;
}

/*
 * proxy_get - gets next message from DataEntry Backend
 * identity parameter is mandatory
 */ 
function proxy_get(identity, callback)
{
    var proxy_answer = {'text': 'dumb'};
    $.ajax({
        type: 'POST',
        url: proxy_url ,
        data: {'identity': identity, 'action': 'list'},
        dataType: 'json',
        success: callback
    });
    return proxy_answer;
}
