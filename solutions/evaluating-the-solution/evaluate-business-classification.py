def evaluate_business_classification(
    business_category_list: List[Optional[GeneralInfo]], data: pd.DataFrame
) -> float:
    """Return accuracy of classification of whether an article is about business.

    Data should contain:
    - a column "is_business" with a boolean indicating whether the article is about business.

    The provided list of business categories should be in the same order as the data.
    """

    correct = 0
    incorrect = 0
    for i, row in data.iterrows():
        if business_category_list[i] is None:
            continue

        is_about_business_prediction = business_category_list[i].is_about_business
        if is_about_business_prediction == row["is_business"]:
            correct += 1
        else:
            incorrect += 1

    accuracy = correct / (correct + incorrect)
    return accuracy
