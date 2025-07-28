from ai_book_seeker.features.search_faq.schema import FAQAnswer, FAQOutputSchema


def combine_and_format_faq_results(semantic_results, keyword_results):
    """
    Combine semantic and keyword FAQ search results, deduplicate, and format as FAQOutputSchema.

    Args:
        semantic_results (list): List of (category, question, answer, similarity) tuples from semantic search.
        keyword_results (list): List of (category, question, answer) tuples from keyword search.

    Returns:
        FAQOutputSchema: Output schema with summary text and answer objects.
    """
    seen = {}
    for res in semantic_results:
        category, q, a, sim = res
        seen[(category, q)] = {"category": category, "question": q, "answer": a, "similarity": sim}

    for category, q, a in keyword_results:
        if (category, q) not in seen:
            seen[(category, q)] = {"category": category, "question": q, "answer": a, "similarity": None}

    answers = list(seen.values())
    if not answers:
        return FAQOutputSchema(text="Sorry, I couldn't find an answer to your question.", data=[])

    top = answers[0]
    text = f"Q: {top['question']}\nA: {top['answer']}"
    answer_objs = [FAQAnswer(**a) for a in answers]
    return FAQOutputSchema(text=text, data=answer_objs)
