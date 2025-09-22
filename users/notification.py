from firebase_admin import messaging

def send_notification_to_user(user, title, body):
    if not user.firebase_token:
        return False
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=user.firebase_token,
    )
    try:
        response = messaging.send(message)
        return response 
    except Exception as e:
        return False