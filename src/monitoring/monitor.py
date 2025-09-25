"""
Main monitoring service for the Wine Management API

This service continuously monitors the API endpoints, collects metrics,
and detects issues and provide insights.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

import aiohttp
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

from .monitoring_agent import MonitoringAgent, MetricData, AlertLevel

logger = logging.getLogger(__name__)
console = Console()


class APIMonitor:
    """
    Main API monitoring service that collects metrics and uses AI analysis.
    """

    def __init__(self, api_base_url: str = "http://localhost:8000", config: Optional[Dict] = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.config = config or {}
        self.monitoring_agent = MonitoringAgent(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitoring_active = False

        # Endpoints to monitor
        self.endpoints = [
            "/",
            "/health",
            "/regions",
            "/wines",
            "/search/wines"
        ]

        # Monitoring intervals
        self.check_interval = self.config.get('check_interval', 30)  # seconds
        self.timeout = self.config.get('timeout', 10)  # seconds

    async def start_monitoring(self) -> None:
        """Start the monitoring service"""
        self.monitoring_active = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

        logger.info("Starting API monitoring for %s", self.api_base_url)
        console.print(f"[green]🔍 Starting API monitoring for {self.api_base_url}[/green]")

        try:
            while self.monitoring_active:
                await self._monitor_endpoints()
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        finally:
            await self.stop_monitoring()

    async def stop_monitoring(self) -> None:
        """Stop the monitoring service"""
        self.monitoring_active = False
        if self.session:
            await self.session.close()
        logger.info("Monitoring service stopped")

    async def _monitor_endpoints(self) -> None:
        """Monitor all configured endpoints"""
        tasks = []
        for endpoint in self.endpoints:
            task = asyncio.create_task(self._check_endpoint(endpoint))
            tasks.append(task)

        # Wait for all endpoint checks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Error monitoring %s: %s", self.endpoints[i], result)
                # Create error metric
                error_metric = MetricData(
                    timestamp=datetime.now(),
                    endpoint=self.endpoints[i],
                    response_time=0,
                    status_code=0,
                    error_count=1
                )
                self.monitoring_agent.add_metric(error_metric)

    async def _check_endpoint(self, endpoint: str) -> None:
        """Check a specific endpoint and collect metrics"""
        url = f"{self.api_base_url}{endpoint}"
        start_time = time.time()

        try:
            async with self.session.get(url) as response:
                response_time = time.time() - start_time

                # Create metric data
                metric = MetricData(
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    response_time=response_time,
                    status_code=response.status,
                    error_count=1 if response.status >= 400 else 0
                )

                # Add to monitoring agent for analysis
                self.monitoring_agent.add_metric(metric)

                logger.debug("Checked %s: %s (%.3fs)", endpoint, response.status, response_time)

        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            metric = MetricData(
                timestamp=datetime.now(),
                endpoint=endpoint,
                response_time=response_time,
                status_code=408,  # Request Timeout
                error_count=1
            )
            self.monitoring_agent.add_metric(metric)
            logger.warning("Timeout checking %s", endpoint)

        except Exception as e:
            response_time = time.time() - start_time
            metric = MetricData(
                timestamp=datetime.now(),
                endpoint=endpoint,
                response_time=response_time,
                status_code=0,  # Connection error
                error_count=1
            )
            self.monitoring_agent.add_metric(metric)
            logger.error("Error checking %s: %s", endpoint, e)

    def get_status_report(self) -> Dict[str, Any]:
        """Get a comprehensive status report"""
        health_summary = self.monitoring_agent.get_health_summary()
        recent_alerts = self.monitoring_agent.get_recent_alerts(hours=24)

        return {
            "monitoring_active": self.monitoring_active,
            "api_base_url": self.api_base_url,
            "endpoints_monitored": self.endpoints,
            "check_interval": self.check_interval,
            "health_summary": health_summary,
            "recent_alerts": [asdict(alert) for alert in recent_alerts],
            "total_metrics_collected": len(self.monitoring_agent.metrics_history),
            "baseline_metrics": self.monitoring_agent.baseline_metrics
        }

    def display_dashboard(self) -> None:
        """Display a real-time monitoring dashboard"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        layout["left"].split_column(
            Layout(name="health"),
            Layout(name="metrics")
        )

        layout["right"].split_column(
            Layout(name="alerts"),
            Layout(name="insights")
        )

        with Live(layout, refresh_per_second=1, console=console):
            while self.monitoring_active:
                # Update header
                layout["header"].update(
                    Panel(
                        f"[bold blue]🍷 Wine API Monitor[/bold blue] | "
                        f"[green]{self.api_base_url}[/green] | "
                        f"[yellow]{datetime.now().strftime('%H:%M:%S')}[/yellow]",
                        style="blue"
                    )
                )

                # Update health status
                health_summary = self.monitoring_agent.get_health_summary()
                status_color = "green" if health_summary["status"] == "healthy" else "yellow" if health_summary["status"] == "degraded" else "red"

                health_text = f"""
[bold]Status:[/bold] [{status_color}]{health_summary['status'].upper()}[/{status_color}]
[bold]Health Score:[/bold] {health_summary['health_score']}/100
[bold]Avg Response Time:[/bold] {health_summary.get('avg_response_time', 0):.3f}s
[bold]Error Rate:[/bold] {health_summary.get('error_rate', 0):.1%}
[bold]Active Alerts:[/bold] {health_summary.get('active_alerts', 0)}
"""
                layout["health"].update(Panel(health_text, title="Health Status", border_style=status_color))

                # Update metrics table
                metrics_table = Table(title="Recent Metrics")
                metrics_table.add_column("Endpoint", style="cyan")
                metrics_table.add_column("Avg RT", style="magenta")
                metrics_table.add_column("Success Rate", style="green")
                metrics_table.add_column("Last Updated", style="yellow")

                for endpoint, baseline in self.monitoring_agent.baseline_metrics.items():
                    metrics_table.add_row(
                        endpoint,
                        f"{baseline['avg_response_time']:.3f}s",
                        f"{baseline['success_rate']:.1%}",
                        baseline['last_updated'].strftime('%H:%M:%S')
                    )

                layout["metrics"].update(metrics_table)

                # Update alerts
                recent_alerts = self.monitoring_agent.get_recent_alerts(hours=1)
                alerts_text = ""
                if recent_alerts:
                    for alert in recent_alerts[-5:]:  # Show last 5 alerts
                        alert_color = "red" if alert.level == AlertLevel.CRITICAL else "yellow" if alert.level == AlertLevel.WARNING else "blue"
                        alerts_text += f"[{alert_color}]• {alert.title}[/{alert_color}]\n{alert.description}\n\n"
                else:
                    alerts_text = "[green]No recent alerts[/green]"

                layout["alerts"].update(Panel(alerts_text, title="Recent Alerts", border_style="yellow"))

                # Update insights
                insights_text = ""
                if health_summary.get('insights'):
                    for insight in health_summary['insights']:
                        insights_text += f"• {insight}\n"
                else:
                    insights_text = "No insights available"

                layout["insights"].update(Panel(insights_text, title="AI Insights", border_style="blue"))

                # Update footer
                layout["footer"].update(
                    Panel(
                        f"[dim]Press Ctrl+C to stop monitoring | "
                        f"Metrics collected: {len(self.monitoring_agent.metrics_history)} | "
                        f"Check interval: {self.check_interval}s[/dim]",
                        style="dim"
                    )
                )

                time.sleep(1)


@click.group()
def cli():
    """Wine API Monitoring Tool"""
    pass


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to monitor')
@click.option('--interval', default=30, help='Check interval in seconds')
@click.option('--timeout', default=10, help='Request timeout in seconds')
@click.option('--dashboard', is_flag=True, help='Show real-time dashboard')
def monitor(api_url: str, interval: int, timeout: int, dashboard: bool):
    """Start monitoring the Wine API"""
    config = {
        'check_interval': interval,
        'timeout': timeout,
        'response_time_threshold': 2.0,
        'error_rate_threshold': 0.05,
        'anomaly_sensitivity': 2.0
    }

    monitor_service = APIMonitor(api_url, config)

    if dashboard:
        # Start dashboard in a separate task
        async def run_dashboard():
            await monitor_service.start_monitoring()

        asyncio.run(run_dashboard())
    else:
        # Simple monitoring without dashboard
        async def run_monitoring():
            await monitor_service.start_monitoring()

        asyncio.run(run_monitoring())


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to check')
def health(api_url: str):
    """Check API health status"""
    async def check_health():
        config = {'check_interval': 5, 'timeout': 10}
        monitor_service = APIMonitor(api_url, config)

        # Run a quick health check
        monitor_service.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )

        try:
            await monitor_service._monitor_endpoints()
            report = monitor_service.get_status_report()

            console.print("\n[bold blue]🍷 Wine API Health Report[/bold blue]")
            console.print(f"API URL: {api_url}")
            console.print(f"Status: {report['health_summary']['status']}")
            console.print(f"Health Score: {report['health_summary']['health_score']}/100")

            if report['recent_alerts']:
                console.print("\n[bold red]Recent Alerts:[/bold red]")
                for alert in report['recent_alerts'][-3:]:
                    console.print(f"• {alert['title']}: {alert['description']}")

        finally:
            await monitor_service.session.close()

    asyncio.run(check_health())


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to test')
@click.option('--count', default=10, help='Number of test requests')
def test(api_url: str, count: int):
    """Run a quick load test on the API"""
    async def run_test():
        config = {'check_interval': 1, 'timeout': 5}
        monitor_service = APIMonitor(api_url, config)

        monitor_service.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        )

        console.print(f"[bold blue]🧪 Running load test on {api_url}[/bold blue]")
        console.print(f"Test requests: {count}")

        try:
            for i in range(count):
                await monitor_service._monitor_endpoints()
                console.print(f"Request {i+1}/{count} completed")
                await asyncio.sleep(0.5)

            report = monitor_service.get_status_report()
            console.print("\n[bold green]Test Results:[/bold green]")
            console.print(f"Total metrics: {report['total_metrics_collected']}")
            console.print(f"Health score: {report['health_summary']['health_score']}/100")
            console.print(f"Avg response time: {report['health_summary'].get('avg_response_time', 0):.3f}s")

        finally:
            await monitor_service.session.close()

    asyncio.run(run_test())


if __name__ == "__main__":
    cli()
