class BusinessSpecificInfo(BaseModel):
    business: str = Field(..., description="The business or company involved")
    stock_price_change: Literal["increase", "decrease", "none"] = Field(
        ...,
        description="""
        Possible stock price change as result of the article.
        - "increase" if article speaks positively about the business
        - "decrease" if article speaks negatively about the business
        - "none" if article speaks neutrally about the business
        """,
    )
    reason: str = Field(
        ..., description="A single sentence reason for the possible stock price change"
    )
    relevant_substring: str = Field(
        ..., description="A relevant substring from the article supporting the reason (10-20 words)"
    )


class ArticleInfo(BaseModel):
    title: str = Field(..., description="The title of the article")
    summary: str = Field(..., description="A single sentence summary of the article")
    is_about_business: bool = Field(..., description="Whether the article is about business")
    business_info: List[BusinessSpecificInfo]
