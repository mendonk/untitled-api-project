#!/usr/bin/env python3
"""
Startup script for the Wine API Monitoring Application

This script provides easy commands to start different components of the monitoring system.
"""

import asyncio
import logging
import sys
from pathlib import Path

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.monitor import APIMonitor
from monitoring.dashboard import dashboard_app
from monitoring.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Wine API Monitoring System"""
    pass


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to monitor')
@click.option('--interval', default=30, help='Check interval in seconds')
@click.option('--timeout', default=10, help='Request timeout in seconds')
def monitor(api_url: str, interval: int, timeout: int):
    """Start monitoring the Wine API (console mode)"""
    config.set('api.base_url', api_url)
    config.set('monitoring.check_interval', interval)
    config.set('api.timeout', timeout)

    monitor_config = {
        'check_interval': interval,
        'timeout': timeout,
        'response_time_threshold': config.get('monitoring_agent.response_time_threshold', 2.0),
        'error_rate_threshold': config.get('monitoring_agent.error_rate_threshold', 0.05),
        'anomaly_sensitivity': config.get('monitoring_agent.anomaly_sensitivity', 2.0)
    }

    monitor_service = APIMonitor(api_url, monitor_config)

    async def run_monitoring():
        await monitor_service.start_monitoring()

    try:
        asyncio.run(run_monitoring())
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to monitor')
@click.option('--interval', default=30, help='Check interval in seconds')
@click.option('--timeout', default=10, help='Request timeout in seconds')
@click.option('--port', default=8080, help='Dashboard port')
def dashboard(api_url: str, interval: int, timeout: int, port: int):
    """Start monitoring with web dashboard"""
    import uvicorn

    config.set('api.base_url', api_url)
    config.set('monitoring.check_interval', interval)
    config.set('api.timeout', timeout)

    logger.info("Starting monitoring dashboard on port %s", port)
    logger.info("Dashboard will be available at: http://localhost:%s", port)
    logger.info("Monitoring API at: %s", api_url)

    uvicorn.run(dashboard_app, host="0.0.0.0", port=port)


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to check')
def health(api_url: str):
    """Quick health check of the Wine API"""
    async def check_health():
        import aiohttp

        monitor_config = {'check_interval': 5, 'timeout': 10}
        monitor_service = APIMonitor(api_url, monitor_config)

        monitor_service.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )

        try:
            await monitor_service._monitor_endpoints()
            report = monitor_service.get_status_report()

            print("\n🍷 Wine API Health Report")
            print(f"API URL: {api_url}")
            print(f"Status: {report['health_summary']['status']}")
            print(f"Health Score: {report['health_summary']['health_score']}/100")
            print(f"Avg Response Time: {report['health_summary'].get('avg_response_time', 0):.3f}s")
            print(f"Error Rate: {report['health_summary'].get('error_rate', 0):.1%}")

            if report['recent_alerts']:
                print(f"\n⚠️  Recent Alerts ({len(report['recent_alerts'])}):")
                for alert in report['recent_alerts'][-3:]:
                    print(f"  • {alert['title']}: {alert['description']}")
            else:
                print("\n✅ No recent alerts")

            if report['health_summary'].get('insights'):
                print(f"\n🤖 AI Insights:")
                for insight in report['health_summary']['insights']:
                    print(f"  • {insight}")

        finally:
            await monitor_service.session.close()

    asyncio.run(check_health())


@cli.command()
@click.option('--api-url', default='http://localhost:8000', help='API base URL to test')
@click.option('--count', default=10, help='Number of test requests')
def test(api_url: str, count: int):
    """Run a load test on the Wine API"""
    async def run_test():
        import aiohttp

        monitor_config = {'check_interval': 1, 'timeout': 5}
        monitor_service = APIMonitor(api_url, monitor_config)

        monitor_service.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        )

        print(f"🧪 Running load test on {api_url}")
        print(f"Test requests: {count}")

        try:
            for i in range(count):
                await monitor_service._monitor_endpoints()
                print(f"Request {i+1}/{count} completed")
                await asyncio.sleep(0.5)

            report = monitor_service.get_status_report()
            print(f"\n📊 Test Results:")
            print(f"Total metrics: {report['total_metrics_collected']}")
            print(f"Health score: {report['health_summary']['health_score']}/100")
            print(f"Avg response time: {report['health_summary'].get('avg_response_time', 0):.3f}s")
            print(f"Error rate: {report['health_summary'].get('error_rate', 0):.1%}")

            if report['recent_alerts']:
                print(f"\n⚠️  Alerts generated:")
                for alert in report['recent_alerts']:
                    print(f"  • {alert['title']}: {alert['description']}")

        finally:
            await monitor_service.session.close()

    asyncio.run(run_test())


@cli.command()
def init():
    """Initialize monitoring configuration"""
    config.create_sample_config()
    print("✅ Monitoring configuration initialized")
    print("📝 Edit monitoring_config.yaml to customize settings")


@cli.command()
def status():
    """Show current monitoring configuration"""
    print("📋 Current Monitoring Configuration:")
    print(f"  API URL: {config.get('api.base_url')}")
    print(f"  Check Interval: {config.get('monitoring.check_interval')}s")
    print(f"  Timeout: {config.get('api.timeout')}s")
    print(f"  Response Time Threshold: {config.get('monitoring_agent.response_time_threshold')}s")
    print(f"  Error Rate Threshold: {config.get('monitoring_agent.error_rate_threshold')}")
    print(f"  Anomaly Sensitivity: {config.get('monitoring_agent.anomaly_sensitivity')}")


if __name__ == "__main__":
    cli()
