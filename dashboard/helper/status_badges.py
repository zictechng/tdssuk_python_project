
def get_status_badge(status: str) -> str:
    mapping = {
        # shared statuses
        "pending": "warning",
        "read": "info",
        "processing": "info",

        "completed": "success",
        "delivered": "success",
        "replied": "success",

        "failed": "danger",
        "deleted": "danger",
        "cancelled": "danger",
        "close": "danger",
        "rejected": "danger",
    }

    if not status:
        return "secondary"

    return mapping.get(status.strip().lower(), "secondary")