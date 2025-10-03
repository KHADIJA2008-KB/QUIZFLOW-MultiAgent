"""
Notification Tools for QuizFlow
Integrates with Google Calendar API and Twilio/WhatsApp API for reminders and alerts
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, ClassVar
from crewai.tools import BaseTool
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from twilio.rest import Client as TwilioClient
import json


class GoogleCalendarTool(BaseTool):
    """Tool for scheduling quiz reminders in Google Calendar"""
    
    name: str = "Google Calendar Tool"
    description: str = "Schedule quiz reminders and study sessions in Google Calendar"
    
    # Google Calendar API scopes
    SCOPES: ClassVar[List[str]] = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        super().__init__()
        # Don't initialize service in __init__ to avoid Pydantic issues
    
    def _get_service(self):
        """Get Google Calendar service instance"""
        return self._initialize_calendar_api()
    
    def _initialize_calendar_api(self):
        """Initialize Google Calendar API service"""
        try:
            creds = None
            token_path = os.getenv('GOOGLE_CALENDAR_TOKEN_PATH', 'token.json')
            credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH', 'credentials.json')
            
            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            # If there are no (valid) credentials available, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print("Google Calendar credentials not found. Calendar features will be disabled.")
                    return
                
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar API initialized successfully")
            return service
            
        except Exception as e:
            print(f"❌ Google Calendar initialization error: {e}")
            print("Note: Calendar features will be disabled without proper configuration")
            return None
    
    def _run(self, action: str, event_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Google Calendar operations"""
        
        service = self._get_service()
        if not service:
            return {"error": "Google Calendar not initialized. Check configuration."}
        
        try:
            if action == "schedule_quiz_reminder":
                return self._schedule_quiz_reminder(service, event_data)
            elif action == "schedule_study_session":
                return self._schedule_study_session(service, event_data)
            elif action == "get_upcoming_events":
                return self._get_upcoming_events(service, event_data.get("days", 7))
            elif action == "cancel_reminder":
                return self._cancel_reminder(service, event_data.get("event_id"))
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Calendar operation failed: {e}"}
    
    def _schedule_quiz_reminder(self, service, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a quiz reminder in Google Calendar"""
        try:
            # Parse reminder time
            reminder_time = event_data.get("reminder_time")
            if isinstance(reminder_time, str):
                reminder_time = datetime.fromisoformat(reminder_time)
            elif not isinstance(reminder_time, datetime):
                # Default to 1 hour from now
                reminder_time = datetime.utcnow() + timedelta(hours=1)
            
            # Create event
            event = {
                'summary': f"📚 Quiz Reminder: {event_data.get('subject', 'Study Session')}",
                'description': f"""
                QuizFlow Quiz Reminder
                
                Subject: {event_data.get('subject', 'General')}
                Difficulty: {event_data.get('difficulty', 'Medium')}
                Estimated Time: {event_data.get('estimated_time', '20')} minutes
                
                Don't forget to take your quiz and continue your learning journey!
                
                Login to QuizFlow: {event_data.get('quiz_url', 'https://localhost:3000')}
                """.strip(),
                'start': {
                    'dateTime': reminder_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (reminder_time + timedelta(minutes=30)).isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 10},
                        {'method': 'email', 'minutes': 30},
                    ],
                },
                'attendees': [
                    {'email': event_data.get('user_email', '')}
                ] if event_data.get('user_email') else [],
            }
            
            # Insert event
            created_event = service.events().insert(
                calendarId='primary', 
                body=event
            ).execute()
            
            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "reminder_time": reminder_time.isoformat(),
                "message": "Quiz reminder scheduled successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to schedule quiz reminder: {e}"}
    
    def _schedule_study_session(self, service, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a study session in Google Calendar"""
        try:
            start_time = event_data.get("start_time")
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            elif not isinstance(start_time, datetime):
                start_time = datetime.utcnow() + timedelta(hours=1)
            
            duration = event_data.get("duration_minutes", 60)
            end_time = start_time + timedelta(minutes=duration)
            
            event = {
                'summary': f"📖 Study Session: {event_data.get('topic', 'Learning')}",
                'description': f"""
                QuizFlow Study Session
                
                Topic: {event_data.get('topic', 'General Study')}
                Focus Areas: {', '.join(event_data.get('focus_areas', []))}
                Goals: {event_data.get('goals', 'Review and practice')}
                
                Recommended Resources:
                {chr(10).join(event_data.get('resources', ['Review your notes', 'Practice quiz questions']))}
                """.strip(),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
            }
            
            created_event = service.events().insert(
                calendarId='primary', 
                body=event
            ).execute()
            
            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "message": "Study session scheduled successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to schedule study session: {e}"}
    
    def _get_upcoming_events(self, service, days: int = 7) -> Dict[str, Any]:
        """Get upcoming QuizFlow events from calendar"""
        try:
            now = datetime.utcnow()
            time_max = now + timedelta(days=days)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=50,
                singleEvents=True,
                orderBy='startTime',
                q='QuizFlow'  # Search for QuizFlow events
            ).execute()
            
            events = events_result.get('items', [])
            
            upcoming_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                upcoming_events.append({
                    'id': event['id'],
                    'summary': event['summary'],
                    'description': event.get('description', ''),
                    'start_time': start,
                    'link': event.get('htmlLink', '')
                })
            
            return {
                "events": upcoming_events,
                "total_count": len(upcoming_events),
                "period_days": days
            }
            
        except Exception as e:
            return {"error": f"Failed to get upcoming events: {e}"}
    
    def _cancel_reminder(self, service, event_id: str) -> Dict[str, Any]:
        """Cancel a scheduled reminder"""
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return {
                "success": True,
                "message": "Reminder cancelled successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to cancel reminder: {e}"}


class TwilioNotificationTool(BaseTool):
    """Tool for sending SMS and WhatsApp notifications via Twilio"""
    
    name: str = "Twilio Notification Tool"
    description: str = "Send SMS and WhatsApp notifications for quiz reminders and achievements"
    
    def __init__(self):
        super().__init__()
        # Don't initialize client in __init__ to avoid Pydantic issues
    
    def _get_client(self):
        """Get Twilio client instance"""
        return self._initialize_twilio()
    
    def _initialize_twilio(self):
        """Initialize Twilio client"""
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            
            if account_sid and auth_token:
                client = TwilioClient(account_sid, auth_token)
                print("✅ Twilio client initialized successfully")
                return client
            else:
                print("❌ Twilio credentials not found. SMS/WhatsApp features will be disabled.")
                return None
                
        except Exception as e:
            print(f"❌ Twilio initialization error: {e}")
            return None
    
    def _run(self, action: str, message_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Twilio operations"""
        
        client = self._get_client()
        if not client:
            return {"error": "Twilio not initialized. Check configuration."}
        
        try:
            if action == "send_sms":
                return self._send_sms(client, message_data)
            elif action == "send_whatsapp":
                return self._send_whatsapp(client, message_data)
            elif action == "send_quiz_reminder":
                return self._send_quiz_reminder(client, message_data)
            elif action == "send_achievement_alert":
                return self._send_achievement_alert(client, message_data)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Twilio operation failed: {e}"}
    
    def _send_sms(self, client, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS message"""
        try:
            message = client.messages.create(
                body=message_data.get("body", ""),
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=message_data.get("to")
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "message": "SMS sent successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to send SMS: {e}"}
    
    def _send_whatsapp(self, client, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp message"""
        try:
            # WhatsApp numbers must be prefixed with 'whatsapp:'
            to_number = message_data.get("to")
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            from_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
            
            message = client.messages.create(
                body=message_data.get("body", ""),
                from_=from_number,
                to=to_number
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "message": "WhatsApp message sent successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to send WhatsApp message: {e}"}
    
    def _send_quiz_reminder(self, client, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send quiz reminder notification"""
        try:
            subject = message_data.get("subject", "your studies")
            user_name = message_data.get("user_name", "Learner")
            quiz_url = message_data.get("quiz_url", "https://localhost:3000")
            
            body = f"""
🎯 QuizFlow Reminder!

Hi {user_name}! Time for your {subject} quiz.

📚 Stay consistent with your learning journey
⏰ Estimated time: {message_data.get('estimated_time', '20')} minutes
🎯 Difficulty: {message_data.get('difficulty', 'Medium')}

Start your quiz: {quiz_url}

Keep up the great work! 💪
            """.strip()
            
            # Send via preferred method
            method = message_data.get("method", "sms")
            if method == "whatsapp":
                return self._send_whatsapp(client, {
                    "to": message_data.get("phone_number"),
                    "body": body
                })
            else:
                return self._send_sms(client, {
                    "to": message_data.get("phone_number"),
                    "body": body
                })
                
        except Exception as e:
            return {"error": f"Failed to send quiz reminder: {e}"}
    
    def _send_achievement_alert(self, client, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send achievement/badge notification"""
        try:
            user_name = message_data.get("user_name", "Learner")
            achievement = message_data.get("achievement", "new milestone")
            badge_name = message_data.get("badge_name", "")
            
            # Create achievement message
            if badge_name:
                body = f"""
🏆 Congratulations {user_name}!

You've earned a new badge: {badge_name}!

🎉 {achievement}
📈 Keep up the excellent progress!
🎯 Continue your learning journey on QuizFlow

You're doing amazing! 🌟
                """.strip()
            else:
                body = f"""
🎊 Great job {user_name}!

Achievement unlocked: {achievement}

📊 Your dedication is paying off!
🚀 Keep pushing your limits!

Continue learning on QuizFlow! 💪
                """.strip()
            
            # Send via preferred method
            method = message_data.get("method", "sms")
            if method == "whatsapp":
                return self._send_whatsapp(client, {
                    "to": message_data.get("phone_number"),
                    "body": body
                })
            else:
                return self._send_sms(client, {
                    "to": message_data.get("phone_number"),
                    "body": body
                })
                
        except Exception as e:
            return {"error": f"Failed to send achievement alert: {e}"}


class NotificationSchedulerTool(BaseTool):
    """Tool for managing notification schedules and preferences"""
    
    name: str = "Notification Scheduler Tool"
    description: str = "Manage notification schedules, preferences, and automated reminders"
    
    def get_calendar_tool(self):
        """Get Google Calendar tool instance"""
        return GoogleCalendarTool()
    
    def get_twilio_tool(self):
        """Get Twilio notification tool instance"""
        return TwilioNotificationTool()
    
    def _run(self, action: str, schedule_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute notification scheduling operations"""
        
        try:
            if action == "schedule_daily_reminder":
                return self._schedule_daily_reminder(schedule_data)
            elif action == "schedule_weekly_summary":
                return self._schedule_weekly_summary(schedule_data)
            elif action == "send_immediate_notification":
                return self._send_immediate_notification(schedule_data)
            elif action == "update_preferences":
                return self._update_notification_preferences(schedule_data)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Notification scheduling failed: {e}"}
    
    def _schedule_daily_reminder(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule daily quiz reminders"""
        try:
            user_preferences = schedule_data.get("preferences", {})
            reminder_time = user_preferences.get("daily_reminder_time", "18:00")  # 6 PM default
            
            # Parse time
            hour, minute = map(int, reminder_time.split(":"))
            
            # Schedule calendar event for tomorrow
            tomorrow = datetime.utcnow().replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
            
            calendar_result = self.get_calendar_tool()._run("schedule_quiz_reminder", {
                "reminder_time": tomorrow,
                "subject": schedule_data.get("subject", "Daily Study"),
                "user_email": schedule_data.get("user_email", ""),
                "quiz_url": schedule_data.get("quiz_url", "https://localhost:3000")
            })
            
            # Schedule SMS/WhatsApp if enabled
            notification_results = []
            if user_preferences.get("sms_enabled", False) and schedule_data.get("phone_number"):
                # In a real implementation, you'd use a task scheduler like Celery
                # For now, we'll just return the configuration
                notification_results.append({
                    "type": "sms",
                    "scheduled_time": tomorrow.isoformat(),
                    "status": "configured"
                })
            
            return {
                "success": True,
                "calendar_event": calendar_result,
                "notifications": notification_results,
                "next_reminder": tomorrow.isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to schedule daily reminder: {e}"}
    
    def _schedule_weekly_summary(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule weekly progress summary"""
        try:
            user_preferences = schedule_data.get("preferences", {})
            summary_day = user_preferences.get("weekly_summary_day", "sunday")  # Default to Sunday
            summary_time = user_preferences.get("weekly_summary_time", "10:00")  # 10 AM default
            
            # Calculate next summary date
            days_ahead = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            
            today = datetime.utcnow()
            days_to_add = (days_ahead[summary_day.lower()] - today.weekday()) % 7
            if days_to_add == 0:  # If it's the same day, schedule for next week
                days_to_add = 7
            
            hour, minute = map(int, summary_time.split(":"))
            next_summary = today.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_to_add)
            
            # Schedule calendar event
            calendar_result = self.get_calendar_tool()._run("schedule_study_session", {
                "start_time": next_summary,
                "duration_minutes": 30,
                "topic": "Weekly Progress Review",
                "goals": "Review weekly progress and plan next week's learning",
                "resources": [
                    "Check your QuizFlow dashboard",
                    "Review completed quizzes",
                    "Plan upcoming study sessions"
                ]
            })
            
            return {
                "success": True,
                "calendar_event": calendar_result,
                "next_summary": next_summary.isoformat(),
                "message": "Weekly summary scheduled successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to schedule weekly summary: {e}"}
    
    def _send_immediate_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send immediate notification"""
        try:
            notification_type = notification_data.get("type", "quiz_reminder")
            method = notification_data.get("method", "sms")
            
            if method in ["sms", "whatsapp"]:
                if notification_type == "quiz_reminder":
                    return self.get_twilio_tool()._run("send_quiz_reminder", notification_data)
                elif notification_type == "achievement":
                    return self.get_twilio_tool()._run("send_achievement_alert", notification_data)
                else:
                    return self.get_twilio_tool()._run("send_sms" if method == "sms" else "send_whatsapp", {
                        "to": notification_data.get("phone_number"),
                        "body": notification_data.get("message", "QuizFlow notification")
                    })
            else:
                return {"error": f"Unsupported notification method: {method}"}
                
        except Exception as e:
            return {"error": f"Failed to send immediate notification: {e}"}
    
    def _update_notification_preferences(self, preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user notification preferences"""
        try:
            # In a real implementation, you'd save these to a database
            # For now, we'll just validate and return the preferences
            
            valid_preferences = {
                "daily_reminder_enabled": preferences_data.get("daily_reminder_enabled", True),
                "daily_reminder_time": preferences_data.get("daily_reminder_time", "18:00"),
                "weekly_summary_enabled": preferences_data.get("weekly_summary_enabled", True),
                "weekly_summary_day": preferences_data.get("weekly_summary_day", "sunday"),
                "weekly_summary_time": preferences_data.get("weekly_summary_time", "10:00"),
                "sms_enabled": preferences_data.get("sms_enabled", False),
                "whatsapp_enabled": preferences_data.get("whatsapp_enabled", False),
                "email_enabled": preferences_data.get("email_enabled", True),
                "achievement_notifications": preferences_data.get("achievement_notifications", True),
                "phone_number": preferences_data.get("phone_number", ""),
                "email": preferences_data.get("email", ""),
                "timezone": preferences_data.get("timezone", "UTC")
            }
            
            return {
                "success": True,
                "preferences": valid_preferences,
                "message": "Notification preferences updated successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to update preferences: {e}"}
