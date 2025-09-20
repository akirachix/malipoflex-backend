from firebase_admin import messaging

def send_notification_to_user(user, title, body):
    """
    Sends a push notification to the specified user's device using Firebase Cloud Messaging.
    Returns the Firebase message ID on success, or False on failure.
    """
    if not user.firebase_token:
        return False
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=user.firebase_token,
    )
    try:
        response = messaging.send(message)
        return response  # This is the message ID string
    except Exception as e:
        # Optionally log the exception: print(f"FCM error: {e}")
        return False