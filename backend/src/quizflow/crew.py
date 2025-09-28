from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pathlib import Path
import json
from typing import Dict, Any, Optional

@CrewBase
class QuizflowCrew:
    """QuizFlow multi-agent crew for automated quiz generation and evaluation"""

    def __init__(self):
        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    # === Agents ===

    @agent
    def quiz_topic_planner(self) -> Agent:
        """Agent responsible for planning quiz topics and subtopics"""
        return Agent(
            config=self.agents_config['quiz_topic_planner'],
            verbose=True
        )

    @agent
    def quiz_maker(self) -> Agent:
        """Agent responsible for generating quiz questions"""
        return Agent(
            config=self.agents_config['quiz_maker'],
            verbose=True
        )

    @agent
    def quiz_checker(self) -> Agent:
        """Agent responsible for evaluating quiz answers"""
        return Agent(
            config=self.agents_config['quiz_checker'],
            verbose=True
        )

    # === Tasks ===

    @task
    def plan_topics_task(self) -> Task:
        """Task to plan topics and subtopics for the quiz"""
        return Task(
            config=self.tasks_config['plan_topics_task'],
            agent=self.quiz_topic_planner(),
            output_file='data/topics.json'
        )

    @task
    def generate_quiz_task(self) -> Task:
        """Task to generate quiz questions based on planned topics"""
        return Task(
            config=self.tasks_config['generate_quiz_task'],
            agent=self.quiz_maker(),
            context=[self.plan_topics_task()],
            output_file='data/quiz.json'
        )

    @task
    def evaluate_quiz_task(self) -> Task:
        """Task to evaluate quiz answers and provide results"""
        return Task(
            config=self.tasks_config['evaluate_quiz_task'],
            agent=self.quiz_checker(),
            context=[self.generate_quiz_task()],
            output_file='data/results.json'
        )

    # === Crew ===

    @crew
    def crew(self) -> Crew:
        """Creates the QuizFlow crew with sequential process"""
        return Crew(
            agents=[
                self.quiz_topic_planner(),
                self.quiz_maker(),
                self.quiz_checker()
            ],
            tasks=[
                self.plan_topics_task(),
                self.generate_quiz_task(),
                self.evaluate_quiz_task()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True
        )

    # === Utility Methods ===

    def generate_quiz_for_subject(self, subject: str) -> Dict[str, Any]:
        """Generate a complete quiz for a given subject"""
        print(f"🚀 Starting quiz generation for subject: {subject}")
        
        # Run the crew with subject input
        inputs = {
            'subject': subject,
            'current_year': '2025'
        }
        
        try:
            result = self.crew().kickoff(inputs=inputs)
            
            # Load generated files and clean JSON
            topics_file = self.data_dir / "topics.json"
            quiz_file = self.data_dir / "quiz.json"
            
            quiz_data = {}
            
            if topics_file.exists():
                quiz_data['topics'] = self._load_and_clean_json(topics_file)
            
            if quiz_file.exists():
                quiz_data['quiz'] = self._load_and_clean_json(quiz_file)
            
            print(f"✅ Quiz generation completed for {subject}")
            return quiz_data
            
        except Exception as e:
            print(f"❌ Error generating quiz: {e}")
            raise

    def _load_and_clean_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file and clean markdown formatting if present"""
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]  # Remove ```
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            # Parse JSON
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Error loading JSON from {file_path}: {e}")
            print(f"File content preview: {content[:200] if 'content' in locals() else 'Could not read file'}")
            raise

    def evaluate_user_answers(self, user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate user answers against the correct answers"""
        print("🔍 Starting quiz evaluation...")
        
        try:
            # The evaluation task will be triggered with user answers as context
            # For now, we'll simulate this by reading the quiz file and comparing answers
            quiz_file = self.data_dir / "quiz.json"
            
            if not quiz_file.exists():
                raise FileNotFoundError("No quiz file found for evaluation")
            
            with open(quiz_file, 'r') as f:
                quiz_data = json.load(f)
            
            # Create a simple evaluation (this would normally be done by the quiz_checker agent)
            results = self._simple_evaluation(quiz_data, user_answers)
            
            # Save results
            results_file = self.data_dir / "results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print("✅ Quiz evaluation completed")
            return results
            
        except Exception as e:
            print(f"❌ Error evaluating quiz: {e}")
            raise

    def _simple_evaluation(self, quiz_data: Dict[str, Any], user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Simple evaluation logic (placeholder for agent-based evaluation)"""
        questions = quiz_data.get('questions', [])
        total_questions = len(questions)
        correct_answers = 0
        question_results = []
        
        for i, question in enumerate(questions):
            question_id = question.get('id', str(i))
            user_answer = user_answers.get(question_id, "")
            correct_answer = question.get('correct_answer', "")
            
            is_correct = False
            if question['type'] in ['multiple_choice', 'true_false']:
                is_correct = user_answer.lower().strip() == correct_answer.lower().strip()
            else:  # short_answer
                # Simple keyword matching for short answers
                is_correct = any(word in user_answer.lower() for word in correct_answer.lower().split())
            
            if is_correct:
                correct_answers += 1
            
            question_results.append({
                "question_id": question_id,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "points_awarded": 1 if is_correct else 0,
                "feedback": f"{'Correct!' if is_correct else 'Incorrect.'} The correct answer is: {correct_answer}"
            })
        
        percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "quiz_results": {
                "user_id": user_answers.get('user_id', 'anonymous'),
                "quiz_id": quiz_data.get('quiz_metadata', {}).get('subject', 'unknown'),
                "timestamp": "2025-01-01T12:00:00Z",  # Would use actual timestamp
                "overall_score": {
                    "points_earned": correct_answers,
                    "total_points": total_questions,
                    "percentage": percentage,
                    "grade": "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
                },
                "question_results": question_results,
                "recommendations": [
                    f"You scored {percentage:.1f}%. Keep practicing to improve!",
                    "Review the questions you got wrong and study those topics more."
                ]
            }
        }
