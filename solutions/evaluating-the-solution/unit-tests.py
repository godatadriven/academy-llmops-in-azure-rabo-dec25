def test_summary_not_too_long(article: str):
    summary = extract_general_info(get_general_info_prompt_template(), article).summary
    assert len(summary.split(". ")) <= 2, f"Summary too long:\n'{summary}'"


def test_extracted_businesses_are_in_article(article: str):
    businesses = extract_businesses_involved(
        get_businesses_involved_prompt_template(), article
    ).businesses
    for business in businesses:
        assert (
            business.lower() in article.lower()
        ), f"Business '{business}' not found in the article"
