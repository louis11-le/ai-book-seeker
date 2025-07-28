import asyncio

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.features.search_faq.faq_service import FAQService
from ai_book_seeker.features.search_faq.logic import combine_and_format_faq_results
from ai_book_seeker.features.search_faq.schema import FAQOutputSchema, FAQSchema

logger = get_logger(__name__)


async def faq_handler(request: FAQSchema, faq_service: FAQService) -> FAQOutputSchema:
    trace_id = getattr(request, "trace_id", None)
    logger.info(f"faq_handler: query={request.query}")
    try:
        semantic_results, keyword_results = await asyncio.gather(
            faq_service.semantic_search_faqs_async(request.query, 3, 0.4),
            asyncio.to_thread(faq_service.search_faqs, request.query),
        )
        response = combine_and_format_faq_results(semantic_results, keyword_results)
        logger.info(f"faq_handler combined results: response={response.dict()} trace_id={trace_id}")
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
