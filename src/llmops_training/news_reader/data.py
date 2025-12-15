import datasets
import pandas as pd
import datetime
from typing import Optional


def get_bbc_news_sample(year_month: Optional[str] = None) -> pd.DataFrame:
    """Download or load BBC news dataset for a given year_month (YYYY-MM).

    Some columns are dropped or altered and a new column `is_business` is added,
    which indicates whether the article is about business.
    """
    if year_month == None:
        year_month = (datetime.date.today() - datetime.timedelta(days=30*12)).strftime("%Y-%m")
    
    dataset = datasets.load_dataset("RealTimeData/bbc_news_alltime", year_month)

    df = (
        pd.DataFrame(dataset["train"])  # There is only train
        .drop_duplicates(subset=["title"])
        .assign(
            is_business=lambda d: d["section"] == "Business",
            article=lambda d: d["title"] + "\n\n" + d["content"].str.replace("\n\n", "\n"),
        )
    )

    n_business = df["is_business"].sum()

    # Sample the same number of business and non-business articles
    sample = (
        df.groupby("is_business", as_index=False)
        .sample(n_business, replace=False, random_state=42)
        .reset_index(drop=True)
    )

    return sample[["article", "is_business", "description", "title"]]


def get_evaluation_data() -> pd.DataFrame:
    """Returns small sample of data for evaluation, balanced in terms of business/non-business.

    We only take a few articles for the sake of example, otherwise evaluations
    would take quite long, or we quickly hit our LLM API rate limits.
    """

    year_month = (datetime.date.today() - datetime.timedelta(days=30*12)).strftime("%Y-%m")

    data = get_bbc_news_sample(year_month=year_month)
    sample = (
        data.groupby("is_business", as_index=False)
        .sample(5, replace=False, random_state=31)
        .reset_index(drop=True)
    )

    return sample
