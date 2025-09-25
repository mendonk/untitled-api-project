#!/usr/bin/env python3
"""
Example script demonstrating the Wine API Monitoring System

This script shows how to use the monitoring system programmatically
and demonstrates the AI agent's capabilities.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.monitor import APIMonitor
from monitoring.monitoring_agent import MonitoringAgent, MetricData, AlertLevel
from monitoring.config import config


async def demonstrate_monitoring():
    """Demonstrate the monitoring system capabilities"""
    
    print("🍷 Wine API Monitoring System Demo")
    print("=" * 50)
    
    # Initialize monitoring
    api_url = "http://localhost:8000"
    monitor_config = {
        'check_interval': 5,
        'timeout': 10,
        'response_time_threshold': 1.0,  # Lower threshold for demo
        'error_rate_threshold': 0.1,
        'anomaly_sensitivity': 1.5
    }
    
    monitor = APIMonitor(api_url, monitor_config)
    
    print(f"📡 Monitoring API at: {api_url}")
    print(f"🔍 Check interval: {monitor_config['check_interval']} seconds")
    print(f"⏱️  Timeout: {monitor_config['timeout']} seconds")
    print()
    
    # Start monitoring session
    import aiohttp
    monitor.session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=monitor_config['timeout'])
    )
    
    try:
        # Run monitoring for a short period
        print("🚀 Starting monitoring...")
        
        for i in range(10):  # Monitor for 10 cycles
            print(f"\n--- Monitoring Cycle {i+1}/10 ---")
            
            # Check all endpoints
            await monitor._monitor_endpoints()
            
            # Get analysis results
            health_summary = monitor.monitoring_agent.get_health_summary()
            recent_alerts = monitor.monitoring_agent.get_recent_alerts(hours=1)
            
            # Display results
            print(f"📊 Health Status: {health_summary['status']}")
            print(f"🎯 Health Score: {health_summary['health_score']}/100")
            print(f"⏱️  Avg Response Time: {health_summary.get('avg_response_time', 0):.3f}s")
            print(f"❌ Error Rate: {health_summary.get('error_rate', 0):.1%}")
            print(f"📈 Total Metrics: {len(monitor.monitoring_agent.metrics_history)}")
            
            # Show alerts
            if recent_alerts:
                print(f"⚠️  Active Alerts: {len(recent_alerts)}")
                for alert in recent_alerts[-2:]:  # Show last 2 alerts
                    print(f"   • {alert.title}: {alert.description}")
            else:
                print("✅ No active alerts")
            
            # Show insights
            if health_summary.get('insights'):
                print("📊 Insights:")
                for insight in health_summary['insights'][:2]:  # Show first 2 insights
                    print(f"   • {insight}")
            
            # Show endpoint performance
            if monitor.monitoring_agent.baseline_metrics:
                print("📋 Endpoint Performance:")
                for endpoint, metrics in list(monitor.monitoring_agent.baseline_metrics.items())[:3]:
                    print(f"   • {endpoint}: {metrics['avg_response_time']:.3f}s avg, {metrics['success_rate']:.1%} success")
            
            await asyncio.sleep(monitor_config['check_interval'])
        
        # Final summary
        print("\n" + "=" * 50)
        print("📋 Final Monitoring Summary")
        print("=" * 50)
        
        final_report = monitor.get_status_report()
        
        print(f"🔍 Total monitoring cycles: 10")
        print(f"📊 Total metrics collected: {final_report['total_metrics_collected']}")
        print(f"🎯 Final health score: {final_report['health_summary']['health_score']}/100")
        print(f"⚠️  Total alerts generated: {len(final_report['recent_alerts'])}")
        
        if final_report['recent_alerts']:
            print("\n📋 Alert Summary:")
            alert_counts = {}
            for alert in final_report['recent_alerts']:
                level = alert['level']
                alert_counts[level] = alert_counts.get(level, 0) + 1
            
            for level, count in alert_counts.items():
                print(f"   • {level.upper()}: {count} alerts")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
    
    finally:
        await monitor.session.close()


async def demonstrate_monitoring_agent():
    """Demonstrate monitoring agent capabilities with synthetic data"""
    
    print("\n📊 Monitoring Agent Capabilities Demo")
    print("=" * 50)
    
    # Create monitoring agent
    agent = MonitoringAgent({
        'response_time_threshold': 1.0,
        'error_rate_threshold': 0.1,
        'anomaly_sensitivity': 2.0
    })
    
    print("🧠 Monitoring Agent initialized with:")
    print("   • Response time threshold: 1.0s")
    print("   • Error rate threshold: 10%")
    print("   • Anomaly sensitivity: 2.0")
    print()
    
    # Simulate normal traffic
    print("📊 Simulating normal API traffic...")
    for i in range(20):
        metric = MetricData(
            timestamp=datetime.now(),
            endpoint="/wines",
            response_time=0.5 + (i % 3) * 0.1,  # Normal variation
            status_code=200
        )
        agent.add_metric(metric)
    
    # Simulate slow responses
    print("🐌 Simulating slow responses...")
    for i in range(5):
        metric = MetricData(
            timestamp=datetime.now(),
            endpoint="/wines",
            response_time=2.5,  # Slow response
            status_code=200
        )
        agent.add_metric(metric)
    
    # Simulate errors
    print("❌ Simulating errors...")
    for i in range(3):
        metric = MetricData(
            timestamp=datetime.now(),
            endpoint="/regions",
            response_time=0.3,
            status_code=500  # Server error
        )
        agent.add_metric(metric)
    
    # Get analysis
    health_summary = agent.get_health_summary()
    recent_alerts = agent.get_recent_alerts(hours=1)
    
    print("\n📋 Analysis Results:")
    print(f"   • Health Status: {health_summary['status']}")
    print(f"   • Health Score: {health_summary['health_score']}/100")
    print(f"   • Active Alerts: {len(recent_alerts)}")
    
    if recent_alerts:
        print("\n⚠️  Generated Alerts:")
        for alert in recent_alerts:
            print(f"   • [{alert.level.value.upper()}] {alert.title}")
            print(f"     {alert.description}")
    
    if health_summary.get('insights'):
        print("\n📊 Insights:")
        for insight in health_summary['insights']:
            print(f"   • {insight}")
    
    print("\n✅ Monitoring Agent demo completed!")


async def main():
    """Main demo function"""
    print("Welcome to the Wine API Monitoring System Demo!")
    print("This demo will show you the capabilities of our monitoring system.")
    print()
    
    # Check if API is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ Wine API is running and accessible")
                else:
                    print("⚠️  Wine API responded with non-200 status")
    except Exception as e:
        print(f"❌ Wine API is not accessible: {e}")
        print("Please start the Wine API first:")
        print("   cd sample_api && python start_api.py")
        return
    
    print()
    
    # Run demos
    await demonstrate_monitoring_agent()
    await demonstrate_monitoring()
    
    print("\n🎉 Demo completed!")
    print("\nTo start monitoring in production:")
    print("   python start_monitor.py dashboard")
    print("\nFor console monitoring:")
    print("   python start_monitor.py monitor --dashboard")


if __name__ == "__main__":
    asyncio.run(main())
