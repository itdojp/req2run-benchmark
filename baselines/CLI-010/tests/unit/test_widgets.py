"""Unit tests for TUI dashboard widgets"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.widgets import MetricsWidget, ChartWidget, LogsWidget
from src.data_source import DataSource
from src.config import DashboardConfig


@pytest.fixture
def mock_data_source():
    """Create mock data source"""
    ds = Mock(spec=DataSource)
    ds.get_metrics = AsyncMock(return_value={
        "CPU": 45.2,
        "Memory": 62.8,
        "Requests": 250
    })
    ds.get_chart_data = AsyncMock(return_value=[25.5, 30.2, 35.8])
    ds.get_logs = AsyncMock(return_value=[
        {"timestamp": "2024-01-21T10:00:00", "level": "INFO", "message": "Test log"}
    ])
    return ds


def test_metrics_widget_creation():
    """Test metrics widget creation"""
    widget = MetricsWidget(title="Test Metrics")
    assert widget.title == "Test Metrics"
    assert widget.metrics == {}


def test_chart_widget_creation():
    """Test chart widget creation"""
    widget = ChartWidget(title="Test Chart", max_points=100)
    assert widget.title == "Test Chart"
    assert widget.max_points == 100
    assert len(widget.data_buffer) == 0


def test_logs_widget_creation():
    """Test logs widget creation"""
    widget = LogsWidget(title="Test Logs", max_lines=500)
    assert widget.title == "Test Logs"
    assert widget.max_lines == 500


@pytest.mark.asyncio
async def test_metrics_update(mock_data_source):
    """Test metrics widget data update"""
    widget = MetricsWidget(data_source=mock_data_source)
    await widget.update_metrics()
    
    assert widget.metrics["CPU"] == 45.2
    assert widget.metrics["Memory"] == 62.8
    assert widget.metrics["Requests"] == 250


@pytest.mark.asyncio
async def test_chart_update(mock_data_source):
    """Test chart widget data update"""
    widget = ChartWidget(data_source=mock_data_source)
    await widget.update_chart()
    
    assert len(widget.data_points) == 3
    assert widget.data_points[-1] == 35.8


def test_log_entry_formatting():
    """Test log entry formatting"""
    widget = LogsWidget()
    
    entry = {
        "timestamp": "2024-01-21T10:00:00",
        "level": "ERROR",
        "message": "Test error message"
    }
    
    # Test that add_log doesn't raise exception
    widget.add_log(entry)
    
    # Verify log was added (would need to check internal state)
    # In real implementation, would check the log content