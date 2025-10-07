"""
Monitoring Agent for API Analysis

This module contains the monitoring agent that analyzes API metrics, detects anomalies,
and provides insights about the wine management API performance.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """Data structure for metric measurements"""
    timestamp: datetime
    endpoint: str
    response_time: float
    status_code: int
    error_count: int = 0
    request_count: int = 1


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    level: AlertLevel
    title: str
    description: str
    endpoint: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class MonitoringAgent:
    """
    Monitoring agent that analyzes API metrics and provides insights.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.metrics_history: List[MetricData] = []
        self.alerts: List[Alert] = []
        self.baseline_metrics: Dict[str, Dict] = {}

        # Analysis thresholds
        self.response_time_threshold = self.config.get('response_time_threshold', 2.0)
        self.error_rate_threshold = self.config.get('error_rate_threshold', 0.05)
        self.anomaly_sensitivity = self.config.get('anomaly_sensitivity', 2.0)

    def add_metric(self, metric: MetricData) -> None:
        """Add a new metric measurement"""
        self.metrics_history.append(metric)

        # Keep only last 1000 metrics to prevent memory issues
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

        # Trigger analysis
        self._analyze_metrics()

    def _analyze_metrics(self) -> None:
        """Analysis of metrics to detect anomalies and issues"""
        if len(self.metrics_history) < 10:
            return  # Need minimum data for analysis

        recent_metrics = self.metrics_history[-50:]  # Last 50 measurements

        # Analyze response times
        self._analyze_response_times(recent_metrics)

        # Analyze error rates
        self._analyze_error_rates(recent_metrics)

        # Detect anomalies using statistical analysis
        self._detect_anomalies(recent_metrics)

        # Update baseline metrics
        self._update_baselines(recent_metrics)

    def _analyze_response_times(self, metrics: List[MetricData]) -> None:
        """Analyze response time patterns"""
        response_times = [m.response_time for m in metrics]
        avg_response_time = statistics.mean(response_times)

        # Check for slow endpoints
        slow_endpoints = [m for m in metrics if m.response_time > self.response_time_threshold]

        if slow_endpoints:
            endpoint_counts = {}
            for metric in slow_endpoints:
                endpoint_counts[metric.endpoint] = endpoint_counts.get(metric.endpoint, 0) + 1

            for endpoint, count in endpoint_counts.items():
                if count >= 3:  # Multiple slow requests
                    alert = Alert(
                        id=f"slow_response_{endpoint}_{datetime.now().timestamp()}",
                        timestamp=datetime.now(),
                        level=AlertLevel.WARNING,
                        title="Slow Response Times Detected",
                        description=f"Endpoint {endpoint} has {count} slow responses "
                        f"(>{self.response_time_threshold}s) in recent measurements. "
                        f"Average response time: {avg_response_time:.2f}s",
                        endpoint=endpoint,
                        metrics={"avg_response_time": avg_response_time, "slow_count": count}
                    )
                    self._add_alert(alert)

    def _analyze_error_rates(self, metrics: List[MetricData]) -> None:
        """Analyze error rate patterns"""
        total_requests = len(metrics)
        error_requests = [m for m in metrics if m.status_code >= 400]
        error_rate = len(error_requests) / total_requests if total_requests > 0 else 0

        if error_rate > self.error_rate_threshold:
            error_endpoints = {}
            for metric in error_requests:
                error_endpoints[metric.endpoint] = error_endpoints.get(metric.endpoint, 0) + 1

            alert = Alert(
                id=f"high_error_rate_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                level=AlertLevel.CRITICAL if error_rate > 0.1 else AlertLevel.WARNING,
                title="High Error Rate Detected",
                description=f"Error rate is {error_rate:.1%} "
                f"(threshold: {self.error_rate_threshold:.1%}). "
                f"Total errors: {len(error_requests)}/{total_requests}",
                metrics={"error_rate": error_rate, "error_endpoints": error_endpoints}
            )
            self._add_alert(alert)

    def _detect_anomalies(self, metrics: List[MetricData]) -> None:
        """Detect statistical anomalies in metrics"""
        if len(metrics) < 20:
            return

        response_times = [m.response_time for m in metrics]

        # Calculate statistical measures
        mean_rt = statistics.mean(response_times)
        std_rt = statistics.stdev(response_times) if len(response_times) > 1 else 0

        # Detect outliers using z-score
        outliers = []
        for metric in metrics:
            if std_rt > 0:
                z_score = abs((metric.response_time - mean_rt) / std_rt)
                if z_score > self.anomaly_sensitivity:
                    outliers.append(metric)

        if outliers:
            alert = Alert(
                id=f"anomaly_detected_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                title="Response Time Anomalies Detected",
                description=f"Found {len(outliers)} anomalous response times. "
                f"Mean: {mean_rt:.2f}s, StdDev: {std_rt:.2f}s",
                metrics={"outlier_count": len(outliers), "mean_response_time": mean_rt, "std_deviation": std_rt}
            )
            self._add_alert(alert)

    def _update_baselines(self, metrics: List[MetricData]) -> None:
        """Update baseline metrics for comparison"""
        endpoint_metrics = {}

        for metric in metrics:
            if metric.endpoint not in endpoint_metrics:
                endpoint_metrics[metric.endpoint] = []
            endpoint_metrics[metric.endpoint].append(metric)

        for endpoint, endpoint_metrics_list in endpoint_metrics.items():
            response_times = [m.response_time for m in endpoint_metrics_list]
            status_codes = [m.status_code for m in endpoint_metrics_list]

            self.baseline_metrics[endpoint] = {
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "success_rate": len([s for s in status_codes if s < 400]) / len(status_codes),
                "last_updated": datetime.now()
            }

    def _add_alert(self, alert: Alert) -> None:
        """Add alert to the alerts list"""
        # Check if similar alert already exists (avoid spam)
        recent_alerts = [a for a in self.alerts if (datetime.now() - a.timestamp).seconds < 300]
        similar_alerts = [a for a in recent_alerts if a.title == alert.title and a.endpoint == alert.endpoint]

        if not similar_alerts:
            self.alerts.append(alert)
            logger.warning("New alert: %s - %s", alert.title, alert.description)

    def get_health_summary(self) -> Dict[str, Any]:
        """Get AI-generated health summary"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics available for analysis"}

        recent_metrics = self.metrics_history[-100:]  # Last 100 measurements
        total_requests = len(recent_metrics)
        error_requests = len([m for m in recent_metrics if m.status_code >= 400])
        avg_response_time = statistics.mean([m.response_time for m in recent_metrics])

        # Determine overall health status
        health_score = 100
        issues = []

        if avg_response_time > self.response_time_threshold:
            health_score -= 20
            issues.append("Slow response times")

        error_rate = error_requests / total_requests if total_requests > 0 else 0
        if error_rate > self.error_rate_threshold:
            health_score -= 30
            issues.append("High error rate")

        if len(self.alerts) > 5:
            health_score -= 15
            issues.append("Multiple active alerts")

        # Generated insights
        insights = self._generate_insights(recent_metrics)

        return {
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "critical",
            "health_score": max(0, health_score),
            "total_requests": total_requests,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "active_alerts": len([
                a for a in self.alerts 
                if (datetime.now() - a.timestamp).seconds < 3600
            ]),
            "issues": issues,
            "insights": insights,
            "baseline_metrics": self.baseline_metrics
        }

    def _generate_insights(self, metrics: List[MetricData]) -> List[str]:
        """Generate insights about the API performance"""
        insights = []

        if not metrics:
            return insights

        # Analyze endpoint performance
        endpoint_performance = {}
        for metric in metrics:
            if metric.endpoint not in endpoint_performance:
                endpoint_performance[metric.endpoint] = []
            endpoint_performance[metric.endpoint].append(metric.response_time)

        # Find best and worst performing endpoints
        endpoint_avgs = {ep: statistics.mean(times) for ep, times in endpoint_performance.items()}
        best_endpoint = min(endpoint_avgs.items(), key=lambda x: x[1])
        worst_endpoint = max(endpoint_avgs.items(), key=lambda x: x[1])

        insights.append(
            f"Best performing endpoint: {best_endpoint[0]} ({best_endpoint[1]:.2f}s avg)"
        )
        insights.append(
            f"Slowest endpoint: {worst_endpoint[0]} ({worst_endpoint[1]:.2f}s avg)"
        )

        # Analyze time patterns
        recent_hour = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in metrics if m.timestamp > recent_hour]

        if len(recent_metrics) > len(metrics) * 0.8:
            insights.append("High activity detected in the last hour")

        # Performance trends
        if len(metrics) >= 20:
            first_half = metrics[:len(metrics)//2]
            second_half = metrics[len(metrics)//2:]

            first_avg = statistics.mean([m.response_time for m in first_half])
            second_avg = statistics.mean([m.response_time for m in second_half])

            if second_avg > first_avg * 1.2:
                insights.append("⚠️ Response times are trending upward")
            elif second_avg < first_avg * 0.8:
                insights.append("✅ Response times are improving")

        return insights

    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]

    def clear_old_alerts(self, days: int = 7) -> None:
        """Clear alerts older than N days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
