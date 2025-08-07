import uuid
from contextvars import ContextVar
from functools import wraps

# Create a context variable to store the trace ID
trace_id = ContextVar('trace_id', default=None)

def _generate_trace_id():
    """Generate a new UUID for tracing."""
    return str(uuid.uuid4().hex[:8])

def set_trace_id(id: str = None):
    """Set a new trace ID for the current context."""
    if id: # For cross-service tracing
        trace_id.set(id)
    else:
        trace_id.set(_generate_trace_id())
    return trace_id.get()

def get_trace_id():
    """Get the current trace ID."""
    return trace_id.get()

def with_trace(func):
    """Decorator to ensure a trace ID is set for the function call."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if trace_id.get() is None:
            set_trace_id()
        return func(*args, **kwargs)
    return wrapper