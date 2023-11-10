def get_request(event):
    request = event.get("body")
    if request:
        request = json.loads(request)
    else:
        request = event
    return request