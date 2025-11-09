import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module"""
    return logging.getLogger(name)


def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """Log API request"""
    logger.info(
        f"API Request - Method: {method}, Path: {path}, User: {user_id}, Tenant: {tenant_id}"
    )


def log_api_error(
    logger: logging.Logger,
    method: str,
    path: str,
    error: Exception,
    user_id: Optional[str] = None,
):
    """Log API error"""
    logger.error(
        f"API Error - Method: {method}, Path: {path}, User: {user_id}, Error: {str(error)}",
        exc_info=True,
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    collection: str,
    doc_id: Optional[str] = None,
    success: bool = True,
):
    """Log database operation"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"DB Operation - {status}: {operation} on {collection}, ID: {doc_id}")


def log_websocket_event(
    logger: logging.Logger,
    event_type: str,
    connection_id: str,
    message: Optional[str] = None,
):
    """Log WebSocket event"""
    logger.info(
        f"WebSocket - Event: {event_type}, Connection: {connection_id}, Message: {message}"
    )


def log_agent_activity(
    logger: logging.Logger,
    agent_type: str,
    action: str,
    patient_id: Optional[str] = None,
    details: Optional[str] = None,
):
    """Log agent activity"""
    logger.info(
        f"Agent Activity - Type: {agent_type}, Action: {action}, Patient: {patient_id}, Details: {details}"
    )
