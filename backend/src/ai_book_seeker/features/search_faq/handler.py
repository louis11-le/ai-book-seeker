import asyncio

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.features.search_faq.faq_service import FAQService
from ai_book_seeker.features.search_faq.schema import (
    FAQAnswer,
    FAQOutputSchema,
    FAQSchema,
)

logger = get_logger(__name__)


async def faq_handler(request: FAQSchema, faq_service: FAQService) -> FAQOutputSchema:
    trace_id = getattr(request, "trace_id", None)
    logger.info(f"faq_handler: query={request.query}")
    try:
        semantic_results, keyword_results = await asyncio.gather(
            faq_service.semantic_search_faqs_async(request.query, 3, 0.4),
            asyncio.to_thread(faq_service.search_faqs, request.query),
        )
        seen = {}
        for res in semantic_results:
            category, q, a, sim = res
            seen[(category, q)] = {"category": category, "question": q, "answer": a, "similarity": sim}

        for category, q, a in keyword_results:
            if (category, q) not in seen:
                seen[(category, q)] = {"category": category, "question": q, "answer": a, "similarity": None}

        answers = list(seen.values())
        logger.info(f"faq_handler combined results: answers={answers}")
        if not answers:
            response = FAQOutputSchema(text="Sorry, I couldn't find an answer to your question.", data=[])
            logger.info(f"FAQ search response (no results): response={response.dict()} trace_id={trace_id}")
            return response

        top = answers[0]
        text = f"Q: {top['question']}\nA: {top['answer']}"
        answer_objs = [FAQAnswer(**a) for a in answers]
        response = FAQOutputSchema(text=text, data=answer_objs)
        logger.info(f"FAQ search response (success): response={response.dict()} trace_id={trace_id}")
        return response
    except Exception as e:
        logger.error(f"FAQ search error: {str(e)} trace_id={trace_id}", exc_info=True)
        return FAQOutputSchema(text="Internal error. Please try again later.", data=[])


def get_faq_handler_with_app(app):
    """
    Returns a handler that always uses the singleton FAQService from app.state.
    """

    async def handler(request: FAQSchema):
        faq_service = app.state.faq_service
        return await faq_handler(request, faq_service)

    return handler
