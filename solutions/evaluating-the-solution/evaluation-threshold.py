def test_run_evaluation(evaluation_data: pd.DataFrame):
    results = run_evaluation(evaluation_data)

    assert results["general_info_success_rate"] >= 0.8
    assert results["title_accuracy"] >= 0.5
    assert results["business_classification_accuracy"] >= 0.7
    assert results["summarization_rouge_1"] >= 0.15
