from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pathlib import Path
import json
from typing import Dict, Any, Optional

# Import all tools
from .tools.notification_tools import GoogleCalendarTool, TwilioNotificationTool, NotificationSchedulerTool
from .tools.llm_tools import LLMQuestionGeneratorTool, LLMAnswerEvaluatorTool
from .tools.hint_tools import WikipediaHintTool, StackOverflowHintTool, LearningResourcesTool, HintGeneratorTool
from .tools.analytics_tools import GoogleAnalyticsTool, LearningAnalyticsTool

@CrewBase
class QuizflowCrew:
    """QuizFlow notification-focused crew for proactive study companion"""

    def __init__(self):
        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    # === Agents ===

    @agent
    def notification_agent(self) -> Agent:
        """Agent for managing notifications and reminders"""
        return Agent(
            config=self.agents_config['notification_agent'],
            tools=[
                GoogleCalendarTool(),
                TwilioNotificationTool(),
                NotificationSchedulerTool()
            ],
            verbose=True
        )

    # === Tasks ===

    @task
    def schedule_study_reminder_task(self) -> Task:
        """Task to schedule proactive study reminders"""
        return Task(
            config=self.tasks_config['schedule_study_reminder_task'],
            agent=self.notification_agent(),
            output_file='data/reminder_scheduled.json'
        )

    @task
    def send_achievement_notification_task(self) -> Task:
        """Task to send achievement notifications"""
        return Task(
            config=self.tasks_config['send_achievement_notification_task'],
            agent=self.notification_agent(),
            output_file='data/notification_sent.json'
        )

    # === Crew ===

    @crew
    def crew(self) -> Crew:
        """Creates the notification-focused QuizFlow crew"""
        return Crew(
            agents=[
                self.notification_agent()
            ],
            tasks=[
                self.schedule_study_reminder_task(),
                self.send_achievement_notification_task()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True
        )

    # === Utility Methods ===

    def schedule_study_reminder(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a study reminder for a user"""
        try:
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs={
                "user_email": user_data.get("email"),
                "phone_number": user_data.get("phone_number"),
                "subject": user_data.get("subject", "Study Session"),
                "reminder_time": user_data.get("reminder_time"),
                "preferences": user_data.get("preferences", {})
            })
            
            return {
                "success": True,
                "message": "Study reminder scheduled successfully",
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def send_achievement_notification(self, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send achievement notification to user"""
        try:
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs={
                "user_name": achievement_data.get("user_name"),
                "phone_number": achievement_data.get("phone_number"),
                "achievement": achievement_data.get("achievement"),
                "badge_name": achievement_data.get("badge_name"),
                "method": achievement_data.get("method", "sms")
            })
            
            return {
                "success": True,
                "message": "Achievement notification sent successfully",
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def send_immediate_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send immediate notification via SMS/WhatsApp"""
        try:
            scheduler = NotificationSchedulerTool()
            return scheduler._run("send_immediate_notification", notification_data)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def schedule_daily_reminder(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule daily study reminders"""
        try:
            scheduler = NotificationSchedulerTool()
            return scheduler._run("schedule_daily_reminder", user_data)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def schedule_weekly_summary(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule weekly progress summary"""
        try:
            scheduler = NotificationSchedulerTool()
            return scheduler._run("schedule_weekly_summary", user_data)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_notification_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user notification preferences"""
        try:
            scheduler = NotificationSchedulerTool()
            return scheduler._run("update_preferences", preferences)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # === Quiz Generation and Evaluation Methods ===

    def generate_quiz_for_subject(self, subject: str, difficulty: str = "Medium", num_questions: int = 25) -> Dict[str, Any]:
        """Generate a quiz for a given subject"""
        try:
            generator = LLMQuestionGeneratorTool()
            quiz_data = generator._run(
                topic=subject,
                difficulty=difficulty,
                num_questions=num_questions,
                include_coding=subject.lower() in ["python programming", "javascript programming", "computer science"]
            )
            
            if "error" in quiz_data:
                return {"error": quiz_data["error"]}
            
            # Save quiz data to file
            quiz_file = self.data_dir / "quiz.json"
            with open(quiz_file, 'w') as f:
                json.dump(quiz_data, f, indent=2)
            
            return {"quiz": quiz_data}
            
        except Exception as e:
            return {"error": f"Quiz generation failed: {str(e)}"}

    def evaluate_user_answers(self, user_answers: Dict[str, Any], quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate user answers and provide detailed feedback"""
        try:
            evaluator = LLMAnswerEvaluatorTool()
            results = evaluator._run(user_answers, quiz_data)
            
            if "error" in results:
                return {"error": results["error"]}
            
            # Save results to file
            quiz_id = user_answers.get("quiz_id", "unknown")
            results_file = self.data_dir / f"results_{quiz_id}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            return results
            
        except Exception as e:
            return {"error": f"Answer evaluation failed: {str(e)}"}

    def get_learning_hints(self, question: str, user_answer: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Get contextual hints and learning resources for a question"""
        try:
            hint_generator = HintGeneratorTool()
            hints = hint_generator._run(
                question=question,
                correct_answer="",  # Would need to be passed from the quiz data
                user_answer=user_answer,
                difficulty=difficulty,
                topic=topic
            )
            return hints
            
        except Exception as e:
            return {"error": f"Failed to get hints: {str(e)}"}

    def get_learning_resources(self, topic: str, question_type: str = "general") -> Dict[str, Any]:
        """Get comprehensive learning resources for a topic"""
        try:
            resources_tool = LearningResourcesTool()
            resources = resources_tool._run(
                topic=topic,
                question_type=question_type,
                programming_tags=["python", "javascript"] if "programming" in topic.lower() else None
            )
            return resources
            
        except Exception as e:
            return {"error": f"Failed to get learning resources: {str(e)}"}

    def track_user_progress(self, user_id: str, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track user progress and achievements"""
        try:
            # In a real implementation, this would integrate with Firebase or a database
            # For now, we'll simulate progress tracking
            
            if action == "get_user_progress":
                return {
                    "user_id": user_id,
                    "total_quizzes": data.get("total_quizzes", 0),
                    "average_score": data.get("average_score", 0),
                    "subjects_studied": data.get("subjects_studied", []),
                    "badges_earned": data.get("badges_earned", []),
                    "streak_days": data.get("streak_days", 0),
                    "last_activity": data.get("last_activity", "")
                }
            elif action == "get_leaderboard":
                limit = data.get("limit", 10) if data else 10
                return {
                    "leaderboard": [
                        {"user_id": f"user_{i}", "score": 100 - i*5, "rank": i+1}
                        for i in range(limit)
                    ]
                }
            else:
                return {
                    "success": True,
                    "action": action,
                    "user_id": user_id,
                    "data": data
                }
                
        except Exception as e:
            return {"error": f"Progress tracking failed: {str(e)}"}

    def send_notification(self, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notifications via various channels"""
        try:
            scheduler = NotificationSchedulerTool()
            return scheduler._run("send_immediate_notification", {
                "type": notification_type,
                **data
            })
            
        except Exception as e:
            return {"error": f"Notification sending failed: {str(e)}"}

    def generate_analytics_report(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analytics reports"""
        try:
            analytics_tool = LearningAnalyticsTool()
            return analytics_tool._run(report_type, data)
            
        except Exception as e:
            return {"error": f"Analytics report generation failed: {str(e)}"}