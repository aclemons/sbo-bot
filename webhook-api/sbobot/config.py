from dataclasses import dataclass


@dataclass
class JenkinsConfiguration:
    webhook_secret: str
    webhook_url: str
