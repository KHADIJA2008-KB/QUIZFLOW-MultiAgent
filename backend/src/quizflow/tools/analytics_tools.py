"""
Analytics Tools for QuizFlow
Integrates with Google Analytics for engagement tracking and progress reports
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange,
    OrderBy,
    Filter,
    FilterExpression
)
from google.oauth2.service_account import Credentials
import json


class GoogleAnalyticsTool(BaseTool):
    """Tool for tracking engagement and generating analytics reports"""
    
    name: str = "Google Analytics Tool"
    description: str = "Track user engagement, quiz performance, and generate comprehensive analytics reports"
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.property_id = os.getenv('GA4_PROPERTY_ID')
        self._initialize_analytics()
    
    def _initialize_analytics(self):
        """Initialize Google Analytics Data API client"""
        try:
            credentials_path = os.getenv('GOOGLE_ANALYTICS_CREDENTIALS_PATH')
            
            if credentials_path and os.path.exists(credentials_path):
                credentials = Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                self.client = BetaAnalyticsDataClient(credentials=credentials)
                print("✅ Google Analytics client initialized successfully")
            else:
                print("❌ Google Analytics credentials not found. Analytics features will be disabled.")
                
        except Exception as e:
            print(f"❌ Google Analytics initialization error: {e}")
    
    def _run(self, action: str, report_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Google Analytics operations"""
        
        if not self.client or not self.property_id:
            return {"error": "Google Analytics not initialized. Check configuration."}
        
        try:
            if action == "get_engagement_report":
                return self._get_engagement_report(report_data)
            elif action == "get_quiz_performance":
                return self._get_quiz_performance_report(report_data)
            elif action == "get_user_journey":
                return self._get_user_journey_report(report_data)
            elif action == "get_learning_insights":
                return self._get_learning_insights(report_data)
            elif action == "track_custom_event":
                return self._track_custom_event(report_data)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Analytics operation failed: {e}"}
    
    def _get_engagement_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get user engagement analytics report"""
        try:
            days = report_data.get("days", 30)
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="deviceCategory"),
                    Dimension(name="country"),
                ],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="sessions"),
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="bounceRate"),
                    Metric(name="engagementRate")
                ],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                order_bys=[OrderBy(dimension={"dimension_name": "date"})]
            )
            
            response = self.client.run_report(request)
            
            # Process response
            engagement_data = {
                "period": f"{start_date} to {end_date}",
                "summary": {},
                "daily_metrics": [],
                "device_breakdown": {},
                "geographic_data": {}
            }
            
            total_users = 0
            total_sessions = 0
            total_page_views = 0
            
            for row in response.rows:
                date = row.dimension_values[0].value
                device = row.dimension_values[1].value
                country = row.dimension_values[2].value
                
                users = int(row.metric_values[0].value)
                sessions = int(row.metric_values[1].value)
                page_views = int(row.metric_values[2].value)
                avg_duration = float(row.metric_values[3].value)
                bounce_rate = float(row.metric_values[4].value)
                engagement_rate = float(row.metric_values[5].value)
                
                total_users += users
                total_sessions += sessions
                total_page_views += page_views
                
                # Daily metrics
                engagement_data["daily_metrics"].append({
                    "date": date,
                    "users": users,
                    "sessions": sessions,
                    "page_views": page_views,
                    "avg_session_duration": avg_duration,
                    "engagement_rate": engagement_rate
                })
                
                # Device breakdown
                if device not in engagement_data["device_breakdown"]:
                    engagement_data["device_breakdown"][device] = {"users": 0, "sessions": 0}
                engagement_data["device_breakdown"][device]["users"] += users
                engagement_data["device_breakdown"][device]["sessions"] += sessions
                
                # Geographic data
                if country not in engagement_data["geographic_data"]:
                    engagement_data["geographic_data"][country] = {"users": 0, "sessions": 0}
                engagement_data["geographic_data"][country]["users"] += users
                engagement_data["geographic_data"][country]["sessions"] += sessions
            
            # Summary statistics
            engagement_data["summary"] = {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_page_views": total_page_views,
                "avg_sessions_per_user": total_sessions / total_users if total_users > 0 else 0,
                "avg_page_views_per_session": total_page_views / total_sessions if total_sessions > 0 else 0
            }
            
            return engagement_data
            
        except Exception as e:
            return {"error": f"Failed to get engagement report: {e}"}
    
    def _get_quiz_performance_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get quiz-specific performance analytics"""
        try:
            days = report_data.get("days", 30)
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Custom events for quiz tracking
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[
                    Dimension(name="eventName"),
                    Dimension(name="customEvent:quiz_subject"),
                    Dimension(name="customEvent:quiz_difficulty"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                    Metric(name="totalUsers"),
                ],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.CONTAINS,
                            value="quiz_"
                        )
                    )
                )
            )
            
            response = self.client.run_report(request)
            
            quiz_analytics = {
                "period": f"{start_date} to {end_date}",
                "quiz_events": {},
                "subject_performance": {},
                "difficulty_analytics": {},
                "conversion_funnel": {}
            }
            
            for row in response.rows:
                event_name = row.dimension_values[0].value
                subject = row.dimension_values[1].value
                difficulty = row.dimension_values[2].value
                event_count = int(row.metric_values[0].value)
                users = int(row.metric_values[1].value)
                
                # Event tracking
                if event_name not in quiz_analytics["quiz_events"]:
                    quiz_analytics["quiz_events"][event_name] = {"count": 0, "users": 0}
                quiz_analytics["quiz_events"][event_name]["count"] += event_count
                quiz_analytics["quiz_events"][event_name]["users"] += users
                
                # Subject performance
                if subject and subject != "(not set)":
                    if subject not in quiz_analytics["subject_performance"]:
                        quiz_analytics["subject_performance"][subject] = {"events": 0, "users": 0}
                    quiz_analytics["subject_performance"][subject]["events"] += event_count
                    quiz_analytics["subject_performance"][subject]["users"] += users
                
                # Difficulty analytics
                if difficulty and difficulty != "(not set)":
                    if difficulty not in quiz_analytics["difficulty_analytics"]:
                        quiz_analytics["difficulty_analytics"][difficulty] = {"events": 0, "users": 0}
                    quiz_analytics["difficulty_analytics"][difficulty]["events"] += event_count
                    quiz_analytics["difficulty_analytics"][difficulty]["users"] += users
            
            # Calculate conversion funnel
            events = quiz_analytics["quiz_events"]
            quiz_analytics["conversion_funnel"] = {
                "quiz_started": events.get("quiz_started", {}).get("count", 0),
                "quiz_submitted": events.get("quiz_submitted", {}).get("count", 0),
                "quiz_completed": events.get("quiz_completed", {}).get("count", 0),
                "completion_rate": (
                    events.get("quiz_completed", {}).get("count", 0) / 
                    events.get("quiz_started", {}).get("count", 1) * 100
                ),
                "submission_rate": (
                    events.get("quiz_submitted", {}).get("count", 0) / 
                    events.get("quiz_started", {}).get("count", 1) * 100
                )
            }
            
            return quiz_analytics
            
        except Exception as e:
            return {"error": f"Failed to get quiz performance report: {e}"}
    
    def _get_user_journey_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get user journey and behavior flow analytics"""
        try:
            days = report_data.get("days", 30)
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[
                    Dimension(name="pagePath"),
                    Dimension(name="previousPagePath"),
                    Dimension(name="userType"),
                ],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="uniquePageviews"),
                    Metric(name="averageTimeOnPage"),
                    Metric(name="exitRate")
                ],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                order_bys=[
                    OrderBy(metric={"metric_name": "screenPageViews"}, desc=True)
                ],
                limit=100
            )
            
            response = self.client.run_report(request)
            
            journey_data = {
                "period": f"{start_date} to {end_date}",
                "page_performance": [],
                "user_flow": {},
                "user_types": {"new": {}, "returning": {}},
                "popular_paths": []
            }
            
            for row in response.rows:
                page_path = row.dimension_values[0].value
                previous_page = row.dimension_values[1].value
                user_type = row.dimension_values[2].value
                
                page_views = int(row.metric_values[0].value)
                unique_views = int(row.metric_values[1].value)
                avg_time = float(row.metric_values[2].value)
                exit_rate = float(row.metric_values[3].value)
                
                # Page performance
                journey_data["page_performance"].append({
                    "page": page_path,
                    "page_views": page_views,
                    "unique_views": unique_views,
                    "avg_time_on_page": avg_time,
                    "exit_rate": exit_rate
                })
                
                # User flow
                if previous_page != "(entrance)":
                    flow_key = f"{previous_page} -> {page_path}"
                    if flow_key not in journey_data["user_flow"]:
                        journey_data["user_flow"][flow_key] = 0
                    journey_data["user_flow"][flow_key] += page_views
                
                # User type analysis
                user_type_key = "new" if user_type == "new" else "returning"
                if page_path not in journey_data["user_types"][user_type_key]:
                    journey_data["user_types"][user_type_key][page_path] = 0
                journey_data["user_types"][user_type_key][page_path] += page_views
            
            # Sort popular paths
            journey_data["popular_paths"] = sorted(
                journey_data["user_flow"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return journey_data
            
        except Exception as e:
            return {"error": f"Failed to get user journey report: {e}"}
    
    def _get_learning_insights(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive learning analytics and insights"""
        try:
            # Combine multiple reports for comprehensive insights
            engagement_report = self._get_engagement_report(report_data)
            quiz_performance = self._get_quiz_performance_report(report_data)
            user_journey = self._get_user_journey_report(report_data)
            
            if any("error" in report for report in [engagement_report, quiz_performance, user_journey]):
                return {"error": "Failed to generate comprehensive learning insights"}
            
            insights = {
                "report_period": report_data.get("days", 30),
                "generated_at": datetime.now().isoformat(),
                "key_metrics": {},
                "learning_patterns": {},
                "recommendations": [],
                "trends": {}
            }
            
            # Extract key metrics
            insights["key_metrics"] = {
                "total_learners": engagement_report["summary"]["total_users"],
                "total_quiz_attempts": quiz_performance["conversion_funnel"]["quiz_started"],
                "completion_rate": quiz_performance["conversion_funnel"]["completion_rate"],
                "avg_session_duration": engagement_report["summary"].get("avg_sessions_per_user", 0),
                "engagement_rate": sum(day["engagement_rate"] for day in engagement_report["daily_metrics"]) / len(engagement_report["daily_metrics"]) if engagement_report["daily_metrics"] else 0
            }
            
            # Analyze learning patterns
            insights["learning_patterns"] = {
                "most_popular_subjects": dict(sorted(
                    quiz_performance["subject_performance"].items(),
                    key=lambda x: x[1]["events"],
                    reverse=True
                )[:5]),
                "difficulty_preferences": quiz_performance["difficulty_analytics"],
                "peak_activity_pages": [page["page"] for page in user_journey["page_performance"][:5]],
                "user_retention": {
                    "new_users": sum(engagement_report["geographic_data"].values(), {}),
                    "returning_rate": 0  # Would calculate from actual data
                }
            }
            
            # Generate recommendations
            completion_rate = insights["key_metrics"]["completion_rate"]
            if completion_rate < 50:
                insights["recommendations"].append("Low quiz completion rate. Consider reducing quiz length or improving question clarity.")
            
            if insights["key_metrics"]["engagement_rate"] < 30:
                insights["recommendations"].append("Low engagement rate. Consider adding interactive elements or gamification features.")
            
            # Add more recommendations based on data analysis
            popular_subjects = insights["learning_patterns"]["most_popular_subjects"]
            if popular_subjects:
                top_subject = list(popular_subjects.keys())[0]
                insights["recommendations"].append(f"'{top_subject}' is most popular. Consider expanding content in this area.")
            
            # Identify trends
            daily_metrics = engagement_report["daily_metrics"]
            if len(daily_metrics) >= 7:
                recent_week = daily_metrics[-7:]
                previous_week = daily_metrics[-14:-7] if len(daily_metrics) >= 14 else daily_metrics[:-7]
                
                recent_avg_users = sum(day["users"] for day in recent_week) / 7
                previous_avg_users = sum(day["users"] for day in previous_week) / len(previous_week)
                
                user_trend = ((recent_avg_users - previous_avg_users) / previous_avg_users * 100) if previous_avg_users > 0 else 0
                
                insights["trends"] = {
                    "user_growth_rate": user_trend,
                    "weekly_active_users": recent_avg_users,
                    "trend_direction": "increasing" if user_trend > 5 else "decreasing" if user_trend < -5 else "stable"
                }
            
            return insights
            
        except Exception as e:
            return {"error": f"Failed to generate learning insights: {e}"}
    
    def _track_custom_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track custom events (for future use with Measurement Protocol)"""
        try:
            # This would typically use the Google Analytics Measurement Protocol
            # For now, we'll just validate and return the event structure
            
            required_fields = ["event_name", "user_id"]
            for field in required_fields:
                if field not in event_data:
                    return {"error": f"Missing required field: {field}"}
            
            event_structure = {
                "client_id": event_data.get("user_id"),
                "events": [{
                    "name": event_data.get("event_name"),
                    "parameters": {
                        "quiz_subject": event_data.get("quiz_subject", ""),
                        "quiz_difficulty": event_data.get("quiz_difficulty", ""),
                        "score": event_data.get("score", 0),
                        "completion_time": event_data.get("completion_time", 0),
                        "custom_parameters": event_data.get("custom_parameters", {})
                    }
                }]
            }
            
            return {
                "success": True,
                "event_structure": event_structure,
                "message": "Event structure validated (tracking would be implemented with Measurement Protocol)"
            }
            
        except Exception as e:
            return {"error": f"Failed to track custom event: {e}"}


class LearningAnalyticsTool(BaseTool):
    """Tool for generating detailed learning analytics and progress reports"""
    
    name: str = "Learning Analytics Tool"
    description: str = "Generate comprehensive learning analytics, progress reports, and insights"
    
    def __init__(self):
        super().__init__()
        self.ga_tool = GoogleAnalyticsTool()
    
    def _run(self, analysis_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate learning analytics reports"""
        
        try:
            if analysis_type == "user_progress_report":
                return self._generate_user_progress_report(data)
            elif analysis_type == "subject_performance_analysis":
                return self._analyze_subject_performance(data)
            elif analysis_type == "learning_effectiveness":
                return self._analyze_learning_effectiveness(data)
            elif analysis_type == "engagement_trends":
                return self._analyze_engagement_trends(data)
            else:
                return {"error": f"Unknown analysis type: {analysis_type}"}
                
        except Exception as e:
            return {"error": f"Learning analytics failed: {e}"}
    
    def _generate_user_progress_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive user progress report"""
        try:
            user_id = data.get("user_id")
            days = data.get("days", 30)
            
            # Get analytics data
            analytics_data = self.ga_tool._run("get_learning_insights", {"days": days})
            
            if "error" in analytics_data:
                return analytics_data
            
            # Generate personalized insights
            progress_report = {
                "user_id": user_id,
                "report_period": days,
                "generated_at": datetime.now().isoformat(),
                "performance_summary": {},
                "learning_trajectory": {},
                "achievements": {},
                "recommendations": [],
                "next_steps": []
            }
            
            # Simulate user-specific analysis (would use actual user data in production)
            progress_report["performance_summary"] = {
                "quizzes_completed": data.get("quizzes_completed", 0),
                "average_score": data.get("average_score", 0),
                "time_spent_learning": data.get("time_spent", 0),
                "subjects_studied": data.get("subjects_studied", []),
                "improvement_rate": data.get("improvement_rate", 0)
            }
            
            progress_report["learning_trajectory"] = {
                "difficulty_progression": "progressing from Easy to Medium level",
                "subject_focus": "strong performance in " + (data.get("strongest_subject", "Computer Science")),
                "consistency": "regular learning pattern" if data.get("streak_days", 0) > 7 else "irregular learning pattern",
                "speed": "average pace" if data.get("completion_time", 20) <= 25 else "slower pace"
            }
            
            # Generate personalized recommendations
            avg_score = data.get("average_score", 75)
            if avg_score < 70:
                progress_report["recommendations"].append("Focus on reviewing fundamentals before attempting harder questions")
                progress_report["next_steps"].append("Retake quizzes in weak subject areas")
            elif avg_score > 85:
                progress_report["recommendations"].append("Challenge yourself with harder difficulty levels")
                progress_report["next_steps"].append("Explore advanced topics in your strongest subjects")
            
            return progress_report
            
        except Exception as e:
            return {"error": f"Failed to generate user progress report: {e}"}
    
    def _analyze_subject_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance across different subjects"""
        try:
            # Get quiz performance data
            quiz_analytics = self.ga_tool._run("get_quiz_performance", data)
            
            if "error" in quiz_analytics:
                return quiz_analytics
            
            subject_analysis = {
                "analysis_period": data.get("days", 30),
                "subject_rankings": {},
                "difficulty_distribution": {},
                "improvement_opportunities": [],
                "success_patterns": []
            }
            
            # Analyze subject performance
            subject_performance = quiz_analytics.get("subject_performance", {})
            
            for subject, metrics in subject_performance.items():
                events = metrics.get("events", 0)
                users = metrics.get("users", 1)
                engagement_rate = events / users if users > 0 else 0
                
                subject_analysis["subject_rankings"][subject] = {
                    "total_attempts": events,
                    "unique_users": users,
                    "engagement_rate": engagement_rate,
                    "popularity_rank": 0  # Would calculate actual rank
                }
            
            # Sort by engagement
            sorted_subjects = sorted(
                subject_analysis["subject_rankings"].items(),
                key=lambda x: x[1]["engagement_rate"],
                reverse=True
            )
            
            for i, (subject, metrics) in enumerate(sorted_subjects):
                subject_analysis["subject_rankings"][subject]["popularity_rank"] = i + 1
            
            # Identify improvement opportunities
            low_engagement_subjects = [
                subject for subject, metrics in subject_analysis["subject_rankings"].items()
                if metrics["engagement_rate"] < 2.0
            ]
            
            if low_engagement_subjects:
                subject_analysis["improvement_opportunities"].append({
                    "type": "low_engagement",
                    "subjects": low_engagement_subjects,
                    "recommendation": "Improve content quality or add interactive elements"
                })
            
            # Identify success patterns
            high_engagement_subjects = [
                subject for subject, metrics in subject_analysis["subject_rankings"].items()
                if metrics["engagement_rate"] > 5.0
            ]
            
            if high_engagement_subjects:
                subject_analysis["success_patterns"].append({
                    "type": "high_engagement",
                    "subjects": high_engagement_subjects,
                    "insight": "These subjects have strong learner engagement"
                })
            
            return subject_analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze subject performance: {e}"}
    
    def _analyze_learning_effectiveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall learning effectiveness"""
        try:
            # Get comprehensive analytics
            insights = self.ga_tool._run("get_learning_insights", data)
            
            if "error" in insights:
                return insights
            
            effectiveness_analysis = {
                "overall_effectiveness_score": 0,
                "key_indicators": {},
                "strengths": [],
                "weaknesses": [],
                "improvement_suggestions": []
            }
            
            # Calculate effectiveness score
            completion_rate = insights["key_metrics"]["completion_rate"]
            engagement_rate = insights["key_metrics"]["engagement_rate"]
            
            effectiveness_score = (completion_rate * 0.4 + engagement_rate * 0.6)
            effectiveness_analysis["overall_effectiveness_score"] = effectiveness_score
            
            # Key indicators
            effectiveness_analysis["key_indicators"] = {
                "quiz_completion_rate": completion_rate,
                "user_engagement_rate": engagement_rate,
                "average_session_duration": insights["key_metrics"]["avg_session_duration"],
                "learning_consistency": "high" if completion_rate > 70 else "medium" if completion_rate > 50 else "low"
            }
            
            # Identify strengths and weaknesses
            if completion_rate > 75:
                effectiveness_analysis["strengths"].append("High quiz completion rate indicates good content difficulty balance")
            else:
                effectiveness_analysis["weaknesses"].append("Low completion rate suggests content may be too difficult or too long")
            
            if engagement_rate > 40:
                effectiveness_analysis["strengths"].append("Good user engagement with the platform")
            else:
                effectiveness_analysis["weaknesses"].append("Low engagement rate indicates need for more interactive features")
            
            # Generate improvement suggestions
            if effectiveness_score < 60:
                effectiveness_analysis["improvement_suggestions"].extend([
                    "Consider implementing adaptive difficulty based on user performance",
                    "Add more interactive elements to increase engagement",
                    "Provide immediate feedback to improve learning outcomes"
                ])
            
            return effectiveness_analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze learning effectiveness: {e}"}
    
    def _analyze_engagement_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user engagement trends over time"""
        try:
            # Get engagement data
            engagement_data = self.ga_tool._run("get_engagement_report", data)
            
            if "error" in engagement_data:
                return engagement_data
            
            trends_analysis = {
                "trend_period": data.get("days", 30),
                "overall_trend": "stable",
                "daily_patterns": [],
                "device_preferences": {},
                "geographic_insights": {},
                "actionable_insights": []
            }
            
            # Analyze daily patterns
            daily_metrics = engagement_data.get("daily_metrics", [])
            if len(daily_metrics) > 7:
                # Calculate week-over-week growth
                recent_week = daily_metrics[-7:]
                previous_week = daily_metrics[-14:-7] if len(daily_metrics) >= 14 else daily_metrics[:-7]
                
                recent_avg = sum(day["users"] for day in recent_week) / 7
                previous_avg = sum(day["users"] for day in previous_week) / len(previous_week)
                
                growth_rate = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
                
                if growth_rate > 10:
                    trends_analysis["overall_trend"] = "growing"
                elif growth_rate < -10:
                    trends_analysis["overall_trend"] = "declining"
                
                trends_analysis["daily_patterns"] = {
                    "average_daily_users": recent_avg,
                    "week_over_week_growth": growth_rate,
                    "most_active_day": max(recent_week, key=lambda x: x["users"])["date"],
                    "least_active_day": min(recent_week, key=lambda x: x["users"])["date"]
                }
            
            # Device and geographic insights
            trends_analysis["device_preferences"] = engagement_data.get("device_breakdown", {})
            trends_analysis["geographic_insights"] = engagement_data.get("geographic_data", {})
            
            # Generate actionable insights
            if trends_analysis["overall_trend"] == "declining":
                trends_analysis["actionable_insights"].append("User engagement is declining. Consider running a user feedback survey.")
            elif trends_analysis["overall_trend"] == "growing":
                trends_analysis["actionable_insights"].append("Positive growth trend. Consider scaling successful strategies.")
            
            # Device-specific insights
            device_breakdown = trends_analysis["device_preferences"]
            if device_breakdown.get("mobile", {}).get("users", 0) > device_breakdown.get("desktop", {}).get("users", 0):
                trends_analysis["actionable_insights"].append("Mobile users dominate. Optimize mobile experience further.")
            
            return trends_analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze engagement trends: {e}"}
