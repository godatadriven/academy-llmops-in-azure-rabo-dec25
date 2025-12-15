# Task 1
general_info_prompt_template = get_general_info_prompt_template()
general_info_prompt = format_prompt(general_info_prompt_template, article)
general_info = generate_object(general_info_prompt, GeneralInfo)

# Task 2
business_category_prompt_template = get_business_category_prompt_template()
business_category_prompt = format_prompt(business_category_prompt_template, article)
business_category = generate_object(business_category_prompt, BusinessCategory)

# Task 3
businesses_involved_prompt_template = get_businesses_involved_prompt_template()
businesses_involved_prompt = format_prompt(businesses_involved_prompt_template, article)
businesses_involved = generate_object(businesses_involved_prompt, BusinessesInvolved)

# Task 4
business_info = []
for business in businesses_involved.businesses:
    business_info_prompt_template = get_business_specific_prompt_template()
    prompt = format_prompt(business_info_prompt_template, business=business, article=article)
    business_info.append(generate_object(prompt, BusinessSpecificInfo))  # Task 4

output = ArticleInfo(
    title=general_info.title,
    summary=general_info.summary,
    is_about_business=business_category.is_about_business,
    business_info=business_info,
)
