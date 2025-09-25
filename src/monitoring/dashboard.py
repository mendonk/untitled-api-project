"""
Simple web dashboard for the monitoring application

This provides a web interface to view monitoring data and AI insights.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import aiohttp
from datetime import datetime
from typing import List, Dict, Any
import logging

from .monitor import APIMonitor
from .config import config

logger = logging.getLogger(__name__)

# Create FastAPI app for the dashboard
dashboard_app = FastAPI(
    title="Wine API Monitoring Dashboard",
    description="Real-time monitoring dashboard with analytics and insights",
    version="1.0.0"
)

# Global monitoring instance
monitor_instance: APIMonitor = None
connected_clients: List[WebSocket] = []


async def start_monitoring_background():
    """Start monitoring in the background"""
    global monitor_instance
    if monitor_instance:
        # Initialize the session
        monitor_instance.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=monitor_instance.timeout)
        )
        monitor_instance.monitoring_active = True
        
        try:
            while monitor_instance.monitoring_active:
                await monitor_instance._monitor_endpoints()
                await asyncio.sleep(monitor_instance.check_interval)
        except Exception as e:
            logger.error(f"Background monitoring error: {e}")
        finally:
            if monitor_instance.session:
                await monitor_instance.session.close()


@dashboard_app.on_event("startup")
async def startup_event():
    """Initialize monitoring on startup"""
    global monitor_instance
    api_url = config.get("api.base_url", "http://localhost:8000")
    monitor_config = {
        "check_interval": config.get("monitoring.check_interval", 30),
        "timeout": config.get("api.timeout", 10),
        "response_time_threshold": config.get("monitoring_agent.response_time_threshold", 2.0),
        "error_rate_threshold": config.get("monitoring_agent.error_rate_threshold", 0.05),
        "anomaly_sensitivity": config.get("monitoring_agent.anomaly_sensitivity", 2.0)
    }
    
    monitor_instance = APIMonitor(api_url, monitor_config)
    
    # Start monitoring in the background
    asyncio.create_task(start_monitoring_background())
    logger.info("Dashboard started")


@dashboard_app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wine API Monitor</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .card h3 {
                margin-top: 0;
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                text-transform: uppercase;
            }
            .status.healthy { background-color: #4CAF50; color: white; }
            .status.degraded { background-color: #FF9800; color: white; }
            .status.critical { background-color: #F44336; color: white; }
            .metric {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .metric-value {
                font-weight: bold;
                color: #667eea;
            }
            .alert {
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid;
            }
            .alert.warning { background-color: #fff3cd; border-color: #ffc107; }
            .alert.critical { background-color: #f8d7da; border-color: #dc3545; }
            .alert.info { background-color: #d1ecf1; border-color: #17a2b8; }
            .insight {
                background-color: #e8f5e8;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #28a745;
            }
            .endpoint-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            .endpoint-table th,
            .endpoint-table td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .endpoint-table th {
                background-color: #667eea;
                color: white;
            }
            .refresh-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #28a745;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🍷 Wine API Monitoring Dashboard</h1>
                <p>Real-time monitoring with analytics and insights</p>
            </div>
            
            <div class="refresh-indicator" id="refreshIndicator">
                Last updated: <span id="lastUpdate">--</span>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>Health Status</h3>
                    <div id="healthStatus">
                        <div class="metric">
                            <span>Status:</span>
                            <span class="metric-value" id="status">Loading...</span>
                        </div>
                        <div class="metric">
                            <span>Health Score:</span>
                            <span class="metric-value" id="healthScore">--</span>
                        </div>
                        <div class="metric">
                            <span>Avg Response Time:</span>
                            <span class="metric-value" id="avgResponseTime">--</span>
                        </div>
                        <div class="metric">
                            <span>Error Rate:</span>
                            <span class="metric-value" id="errorRate">--</span>
                        </div>
                        <div class="metric">
                            <span>Active Alerts:</span>
                            <span class="metric-value" id="activeAlerts">--</span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Endpoint Performance</h3>
                    <table class="endpoint-table" id="endpointTable">
                        <thead>
                            <tr>
                                <th>Endpoint</th>
                                <th>Avg RT</th>
                                <th>Success Rate</th>
                            </tr>
                        </thead>
                        <tbody id="endpointTableBody">
                            <tr><td colspan="3">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h3>Recent Alerts</h3>
                    <div id="alertsContainer">
                        <p>Loading alerts...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Analytics Insights</h3>
                    <div id="insightsContainer">
                        <p>Loading insights...</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let ws;
            let reconnectInterval;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    console.log('WebSocket connected');
                    document.getElementById('refreshIndicator').style.backgroundColor = '#28a745';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket disconnected');
                    document.getElementById('refreshIndicator').style.backgroundColor = '#dc3545';
                    
                    // Attempt to reconnect
                    if (!reconnectInterval) {
                        reconnectInterval = setInterval(connectWebSocket, 5000);
                    }
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function updateDashboard(data) {
                // Update health status
                document.getElementById('status').textContent = data.health_summary.status;
                document.getElementById('status').className = `status ${data.health_summary.status}`;
                document.getElementById('healthScore').textContent = `${data.health_summary.health_score}/100`;
                document.getElementById('avgResponseTime').textContent = `${data.health_summary.avg_response_time.toFixed(3)}s`;
                document.getElementById('errorRate').textContent = `${(data.health_summary.error_rate * 100).toFixed(1)}%`;
                document.getElementById('activeAlerts').textContent = data.health_summary.active_alerts;
                
                // Update endpoint table
                const tbody = document.getElementById('endpointTableBody');
                tbody.innerHTML = '';
                
                for (const [endpoint, metrics] of Object.entries(data.baseline_metrics)) {
                    const row = tbody.insertRow();
                    row.insertCell(0).textContent = endpoint;
                    row.insertCell(1).textContent = `${metrics.avg_response_time.toFixed(3)}s`;
                    row.insertCell(2).textContent = `${(metrics.success_rate * 100).toFixed(1)}%`;
                }
                
                // Update alerts
                const alertsContainer = document.getElementById('alertsContainer');
                if (data.recent_alerts && data.recent_alerts.length > 0) {
                    alertsContainer.innerHTML = '';
                    data.recent_alerts.slice(0, 5).forEach(alert => {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = `alert ${alert.level}`;
                        alertDiv.innerHTML = `
                            <strong>${alert.title}</strong><br>
                            ${alert.description}<br>
                            <small>${new Date(alert.timestamp).toLocaleString()}</small>
                        `;
                        alertsContainer.appendChild(alertDiv);
                    });
                } else {
                    alertsContainer.innerHTML = '<p style="color: green;">No recent alerts</p>';
                }
                
                // Update insights
                const insightsContainer = document.getElementById('insightsContainer');
                if (data.health_summary.insights && data.health_summary.insights.length > 0) {
                    insightsContainer.innerHTML = '';
                    data.health_summary.insights.forEach(insight => {
                        const insightDiv = document.createElement('div');
                        insightDiv.className = 'insight';
                        insightDiv.textContent = insight;
                        insightsContainer.appendChild(insightDiv);
                    });
                } else {
                    insightsContainer.innerHTML = '<p>No analytics available</p>';
                }
                
                // Update last update time
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            }
            
            // Connect on page load
            connectWebSocket();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@dashboard_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            if monitor_instance:
                # Get current status
                status_report = monitor_instance.get_status_report()
                
                # Send to client
                await websocket.send_text(json.dumps(status_report, default=str))
            
            await asyncio.sleep(config.get("dashboard.refresh_interval", 1))
            
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)


@dashboard_app.get("/api/status")
async def get_status():
    """API endpoint to get current monitoring status"""
    if monitor_instance:
        return monitor_instance.get_status_report()
    return {"error": "Monitoring not initialized"}


@dashboard_app.get("/api/health")
async def dashboard_health():
    """Dashboard health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(connected_clients),
        "monitoring_active": monitor_instance.monitoring_active if monitor_instance else False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(dashboard_app, host="0.0.0.0", port=8080)
