# Node name and workflow-related constants for orchestrator and workflow graphs

START_NODE = "start"
END_NODE = "end"
ROUTER_NODE = "router_node"
GENERAL_AGENT_NODE = "general_agent"
GENERAL_VOICE_AGENT_NODE = "general_voice_agent"
# SALES_AGENT_NODE = "sales_agent"  # Temporarily disabled
AGENT_COORDINATOR_NODE = "agent_coordinator"
FAQ_TOOL_NODE = "faq_tool"
BOOK_RECOMMENDATION_TOOL_NODE = "book_recommendation_tool"
BOOK_DETAILS_TOOL_NODE = "book_details_tool"
PARAMETER_EXTRACTION_NODE = "parameter_extraction"
FORMAT_RESPONSE_NODE = "format_response"
ERROR_NODE = "error"

# Message type constants for consistent message handling
STREAMING_RESPONSE_MESSAGE_TYPE = "streaming_response"
TOOL_ERROR_MESSAGE_TYPE = "tool_error"
FINAL_RESPONSE_MESSAGE_TYPE = "final_response"
