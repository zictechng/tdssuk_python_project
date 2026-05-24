from django.shortcuts import render

def validation_error(request, message):
    return render(
        request,
        "mainWebsite/partials/message.html",
        {
            "message": message,
            "alert_type": "danger"
        }
    )
    
def error_message(request, message):
    return render(
        request,
        "mainWebsite/partials/message.html",
        {
            "message": message,
            "alert_type": "warning"
        }
    )
    
def success_message(request, message):
    return render(
        request,
        "mainWebsite/partials/message.html",
        {
            "message": message,
            "alert_type": "success",
            "clear_input": True
        }
    )