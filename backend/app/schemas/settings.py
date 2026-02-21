from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    enable_email_notifications: bool
