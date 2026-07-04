from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str
    model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    serper_key: str | None = None
    openrouter_key: str | None = None


class Competitor(BaseModel):
    name: str
    website: str = ""


class PricingItem(BaseModel):
    item: str
    price: str


class Report(BaseModel):
    company_name: str
    website: str = ""
    phone: str = "Not publicly listed"
    address: str = "Not publicly listed"
    summary: str = ""
    products_services: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    pricing: list[PricingItem] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
