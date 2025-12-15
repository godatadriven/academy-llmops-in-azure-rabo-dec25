"""Logging and tracing configuration for News Reader LLMOps.

Uses OpenTelemetry with Application Insights for automatic trace/log collection.
No custom logs ingestion needed - all data flows through OpenTelemetry.
"""

import datetime
import logging
import os
from typing import Any, Dict, List, Literal, Optional

import dotenv
import structlog
from azure.identity import AzureCliCredential
from azure.monitor.opentelemetry.exporter import (
    AzureMonitorTraceExporter,
    AzureMonitorLogExporter
)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

dotenv.load_dotenv()

credential = AzureCliCredential()

# Configuration flags
_tracer_configured = False
_logging_configured = False


def configure_tracer() -> None:
    """Configure OpenTelemetry tracer to export traces to Application Insights."""
    global _tracer_configured
    
    if _tracer_configured:
        return
    
    # Check if already configured by another module
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        _tracer_configured = True
        return
    
    # Configure tracer provider
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)
    
    # Add Azure Monitor exporter
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        azure_exporter = AzureMonitorTraceExporter.from_connection_string(connection_string)
        batch_processor = BatchSpanProcessor(azure_exporter)
        tracer_provider.add_span_processor(batch_processor)
        print("✓ Tracer configured - sending to Application Insights")
    else:
        print("⚠ APPLICATIONINSIGHTS_CONNECTION_STRING not set - traces not exported")
    
    _tracer_configured = True


def configure_structlog() -> None:
    """Configure structlog with OpenTelemetry integration.
    
    Logs are automatically sent to Application Insights via OpenTelemetry.
    No custom logs ingestion needed.
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Configure OpenTelemetry logging exporter
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        # Set up OpenTelemetry logging
        logger_provider = LoggerProvider()
        log_exporter = AzureMonitorLogExporter.from_connection_string(connection_string)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        
        # Attach to Python logging - this is the KEY change
        handler = LoggingHandler(logger_provider=logger_provider)
        
        # Configure root logger to use OpenTelemetry handler
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
            
    # Configure structlog to use stdlib logging as backend
    # This ensures logs flow through Python's logging and get picked up by OTel
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),  # Use stdlib as backend
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    _logging_configured = True


def log_with_trace(
    message: str,
    level: str = "INFO",
    json_payload: Optional[Dict] = None,
    trace_id: Optional[int] = None,
) -> None:
    """Log a message with trace context.
    
    OpenTelemetry automatically propagates trace context to logs.
    """
    current_span = trace.get_current_span()
    span_context = current_span.get_span_context()

    # Get trace ID from context or parameter
    if span_context.is_valid:
        trace_id = span_context.trace_id
    elif trace_id is None:
        # No trace context available - log without trace_id
        logger = structlog.get_logger()
        getattr(logger, level.lower())(message, **json_payload or {})
        return

    # Log with trace context (automatically correlated in App Insights)
    logger = structlog.get_logger()
    log_data = {
        "trace_id": format(trace_id, "032x"),
        "span_id": format(span_context.span_id, "016x") if span_context.is_valid else None,
        **(json_payload or {})
    }
    
    getattr(logger, level.lower())(message, **log_data)


def log_extraction_step(
    event: str,
    article: str,
    prompt_template: str,
    output: dict,
    business: Optional[str] = None
) -> None:
    """Log an LLM extraction step with trace context.
    
    Best practice: Log input/output for debugging and evaluation.
    """
    if not isinstance(output, dict):
        output = output.model_dump()

    json_payload = {
        "article": article[:100],
        "prompt": prompt_template[:200],
        "output": str(output)[:500],
    }
    if business is not None:
        json_payload["business"] = business

    log_with_trace(event, json_payload=json_payload)


def load_feedback_entries(
    feedback: Literal["upvote", "downvote"],
    result_key: Optional[str] = None,
    from_hours_ago: float = 2,
    max_results: int = 5,
    filter_on_user_name: bool = True,
) -> List[Dict[str, Any]]:
    """Load feedback entries from Log Analytics workspace.
    
    Queries custom Feedback_CL table (created by your app's feedback collection).
    """
    from azure.monitor.query import LogsQueryClient
    
    workspace_id = os.getenv("LOG_ANALYTICS_WORKSPACE_ID")
    if not workspace_id:
        print("⚠ LOG_ANALYTICS_WORKSPACE_ID not configured")
        return []
    
    from_datetime = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=from_hours_ago
    )
    
    # Build KQL query
    query = f"""
    Feedback_CL
    | where FeedbackType_s == "{feedback}"
    | where TimeGenerated >= datetime({from_datetime.isoformat()})
    """
    
    if result_key:
        query += f' | where ResultKey_s == "{result_key}"'
    
    if filter_on_user_name:
        user_name = os.getenv("USER_NAME", os.getenv("USER", "unknown"))
        query += f' | where UserName_s == "{user_name}"'
    
    query += f" | order by TimeGenerated desc | take {max_results}"
    
    try:
        logs_query_client = LogsQueryClient(credential=credential)
        response = logs_query_client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=datetime.timedelta(hours=from_hours_ago)
        )
        
        if response.status == "Success" and response.tables:
            columns = [col.name for col in response.tables[0].columns]
            return [dict(zip(columns, row)) for row in response.tables[0].rows]
        else:
            print(f"Query failed: {response.status}")
            return []
    except Exception as e:
        print(f"Error querying feedback: {e}")
        return []


def load_entries_with_feedback(
    feedback: Literal["upvote", "downvote"],
    result_key: Optional[str] = None,
    from_hours_ago: float = 2,
    max_results: int = 5,
    filter_on_user_name: bool = True,
) -> List[Dict[str, Any]]:
    """Load trace entries correlated with feedback.
    
    Joins feedback data with Application Insights traces using trace_id/operation_Id.
    """
    from azure.monitor.query import LogsQueryClient
    
    workspace_id = os.getenv("LOG_ANALYTICS_WORKSPACE_ID")
    if not workspace_id:
        print("⚠ LOG_ANALYTICS_WORKSPACE_ID not configured")
        return []
    
    # Get feedback entries
    feedback_entries = load_feedback_entries(
        feedback, result_key, from_hours_ago, max_results, filter_on_user_name
    )
    
    if not feedback_entries:
        return []
    
    from_datetime = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=from_hours_ago
    )

    entries: List[Dict[str, Any]] = []
    logs_query_client = LogsQueryClient(credential=credential)
    
    for feedback_entry in feedback_entries:
        # Get trace_id from feedback (stored as 32-char hex string)
        trace_id = feedback_entry.get("TraceId_s")
        if not trace_id:
            continue
        
        # Query Application Insights traces by operation_Id (= trace_id)
        query = f"""
        union traces, dependencies, requests
        | where operation_Id == "{trace_id}"
        | where timestamp >= datetime({from_datetime.isoformat()})
        | project timestamp, message, operation_Id, operation_Name, 
                  severityLevel, customDimensions
        | order by timestamp asc
        """
        
        try:
            response = logs_query_client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=datetime.timedelta(hours=from_hours_ago)
            )
            
            if response.status == "Success" and response.tables:
                columns = [col.name for col in response.tables[0].columns]
                for row in response.tables[0].rows:
                    entry = dict(zip(columns, row))
                    entry["feedback"] = feedback
                    entry["feedback_entry"] = feedback_entry
                    entries.append(entry)
                    
        except Exception as e:
            print(f"Error querying traces for {trace_id}: {e}")

    return entries[:max_results]
