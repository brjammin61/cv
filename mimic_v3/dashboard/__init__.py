"""
MIMIC V3.1 Dashboard Package
Bloomberg-style real-time trading monitor
"""

from .api import (
    app,
    dashboard_state,
    ws_manager,
    run_dashboard,
    DashboardState,
    ConnectionManager
)

__all__ = [
    'app',
    'dashboard_state',
    'ws_manager',
    'run_dashboard',
    'DashboardState',
    'ConnectionManager'
]
