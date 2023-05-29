from dataclasses import dataclass


@dataclass
class Company:
    id: int
    name: str
    locality: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    domain: str | None = None

    def update_info(self):
        pass