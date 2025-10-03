"""
LLM Tools for Question Generation and Answer Evaluation
Supports both OpenAI and Google Gemini APIs
"""

import os
import json
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
import openai
import google.generativeai as genai
from pydantic import BaseModel


class LLMQuestionGeneratorTool(BaseTool):
    """Tool for generating quiz questions using LLM APIs"""
    
    name: str = "LLM Question Generator"
    description: str = "Generate diverse quiz questions (MCQs, True/False, coding challenges) using OpenAI or Gemini API"
    preferred_model: str = "openai"
    
    def __init__(self):
        super().__init__()
        # Initialize APIs
        openai.api_key = os.getenv('OPENAI_API_KEY')
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.preferred_model = os.getenv('PREFERRED_LLM', 'openai')  # 'openai' or 'gemini'
    
    def _run(self, topic: str, difficulty: str, num_questions: int = 20, 
             include_coding: bool = False) -> Dict[str, Any]:
        """Generate quiz questions for a given topic and difficulty"""
        
        prompt = self._build_generation_prompt(topic, difficulty, num_questions, include_coding)
        
        try:
            if self.preferred_model == 'gemini' and os.getenv('GEMINI_API_KEY'):
                response = self._generate_with_gemini(prompt)
            else:
                response = self._generate_with_openai(prompt)
            
            return self._parse_response(response)
            
        except Exception as e:
            print(f"Error generating questions: {e}")
            return {"error": str(e)}
    
    def _build_generation_prompt(self, topic: str, difficulty: str, 
                                 num_questions: int, include_coding: bool) -> str:
        """Build the generation prompt for the LLM"""
        
        coding_instruction = """
        - Include 2-3 coding challenges with code snippets to analyze or debug
        - Provide clear problem statements and expected solutions
        """ if include_coding else ""
        
        return f"""
        Generate {num_questions} high-quality quiz questions about {topic} at {difficulty} difficulty level.
        
        Requirements:
        - 60% Multiple Choice Questions (4 options each)
        - 25% True/False Questions
        - 15% Short Answer Questions{coding_instruction}
        
        Each question must include:
        - Clear, unambiguous question text
        - Correct answer
        - For MCQ: 4 plausible options with only one correct
        - Brief explanation (1-2 sentences)
        - Difficulty level: {difficulty}
        - Topic classification
        
        Return ONLY a valid JSON object with this exact structure:
        {{
            "quiz_metadata": {{
                "subject": "{topic}",
                "total_questions": {num_questions},
                "estimated_time_minutes": {max(15, num_questions * 1.5)},
                "difficulty_distribution": {{"Easy": 0, "Medium": 0, "Hard": 0}},
                "includes_coding": {str(include_coding).lower()}
            }},
            "questions": [
                {{
                    "id": "q1",
                    "type": "multiple_choice|true_false|short_answer|coding",
                    "difficulty": "{difficulty}",
                    "topic": "{topic}",
                    "subtopic": "specific_area",
                    "question": "Question text here",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Why this answer is correct",
                    "code_snippet": "// For coding questions only"
                }}
            ]
        }}
        
        Make questions challenging but fair for {difficulty} level. Ensure variety in cognitive levels.
        """
    
    def _generate_with_openai(self, prompt: str) -> str:
        """Generate response using OpenAI API"""
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert educational content creator. Generate high-quality quiz questions that test both theoretical knowledge and practical understanding."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """Generate response using Google Gemini API"""
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4000,
            )
        )
        
        return response.text
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate the LLM response"""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:-3]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:-3]
            
            data = json.loads(cleaned)
            
            # Validate structure
            if "quiz_metadata" not in data or "questions" not in data:
                raise ValueError("Invalid response structure")
            
            # Update difficulty distribution
            difficulty_dist = {"Easy": 0, "Medium": 0, "Hard": 0}
            for question in data["questions"]:
                diff = question.get("difficulty", "Medium")
                if diff in difficulty_dist:
                    difficulty_dist[diff] += 1
            
            data["quiz_metadata"]["difficulty_distribution"] = difficulty_dist
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response preview: {response[:200]}...")
            return {"error": f"Failed to parse JSON response: {e}"}
        except Exception as e:
            print(f"Response parsing error: {e}")
            return {"error": f"Failed to parse response: {e}"}


class LLMAnswerEvaluatorTool(BaseTool):
    """Tool for evaluating quiz answers using LLM APIs"""
    
    name: str = "LLM Answer Evaluator" 
    description: str = "Evaluate quiz answers with detailed feedback and explanations using OpenAI or Gemini API"
    preferred_model: str = "openai"
    
    def __init__(self):
        super().__init__()
        # Initialize APIs
        openai.api_key = os.getenv('OPENAI_API_KEY')
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.preferred_model = os.getenv('PREFERRED_LLM', 'openai')
    
    def _run(self, user_answers: Dict[str, Any], quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate user answers with detailed feedback"""
        
        prompt = self._build_evaluation_prompt(user_answers, quiz_data)
        
        try:
            if self.preferred_model == 'gemini' and os.getenv('GEMINI_API_KEY'):
                response = self._evaluate_with_gemini(prompt)
            else:
                response = self._evaluate_with_openai(prompt)
            
            return self._parse_evaluation_response(response, user_answers, quiz_data)
            
        except Exception as e:
            print(f"Error evaluating answers: {e}")
            return {"error": str(e)}
    
    def _build_evaluation_prompt(self, user_answers: Dict[str, Any], 
                                 quiz_data: Dict[str, Any]) -> str:
        """Build evaluation prompt for the LLM"""
        
        questions = quiz_data.get('quiz', {}).get('questions', quiz_data.get('questions', []))
        
        evaluation_pairs = []
        for question in questions:
            q_id = question.get('id', '')
            user_answer = user_answers.get(q_id, 'No answer provided')
            
            evaluation_pairs.append({
                "question_id": q_id,
                "question_text": question.get('question', ''),
                "question_type": question.get('type', ''),
                "correct_answer": question.get('correct_answer', ''),
                "user_answer": user_answer,
                "options": question.get('options', [])
            })
        
        return f"""
        Evaluate the following quiz answers and provide detailed feedback:
        
        Quiz Context:
        - Subject: {quiz_data.get('quiz_metadata', {}).get('subject', 'Unknown')}
        - Total Questions: {len(questions)}
        
        Evaluation Pairs:
        {json.dumps(evaluation_pairs, indent=2)}
        
        For each question, provide:
        1. Correctness assessment (correct/partially correct/incorrect)
        2. Points awarded (1 for correct, 0.5 for partial, 0 for incorrect)
        3. Detailed feedback explaining why the answer is right/wrong
        4. Learning guidance and tips for improvement
        
        For short answer and coding questions, use semantic understanding to evaluate correctness.
        Consider partial credit for answers that show understanding but miss details.
        
        Return ONLY a valid JSON object with this structure:
        {{
            "quiz_results": {{
                "user_id": "{user_answers.get('user_id', 'anonymous')}",
                "quiz_id": "{user_answers.get('quiz_id', 'unknown')}",
                "timestamp": "2025-01-01T12:00:00Z",
                "overall_score": {{
                    "points_earned": 0,
                    "total_points": {len(questions)},
                    "percentage": 0,
                    "grade": "F"
                }},
                "performance_by_topic": [],
                "performance_by_difficulty": {{
                    "Easy": {{"correct": 0, "total": 0}},
                    "Medium": {{"correct": 0, "total": 0}},
                    "Hard": {{"correct": 0, "total": 0}}
                }},
                "question_results": [
                    {{
                        "question_id": "q1",
                        "user_answer": "user's answer",
                        "correct_answer": "correct answer",
                        "is_correct": true,
                        "points_awarded": 1,
                        "feedback": "Detailed explanation and learning guidance"
                    }}
                ],
                "recommendations": [
                    "Specific study recommendations based on performance"
                ]
            }}
        }}
        """
    
    def _evaluate_with_openai(self, prompt: str) -> str:
        """Evaluate using OpenAI API"""
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert quiz evaluator. Provide fair, detailed assessments with constructive feedback that helps learners improve."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent evaluation
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def _evaluate_with_gemini(self, prompt: str) -> str:
        """Evaluate using Google Gemini API"""
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4000,
            )
        )
        
        return response.text
    
    def _parse_evaluation_response(self, response: str, user_answers: Dict[str, Any], 
                                   quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and enhance the evaluation response"""
        try:
            # Clean response
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:-3]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:-3]
            
            data = json.loads(cleaned)
            
            # Calculate actual scores and statistics
            question_results = data["quiz_results"]["question_results"]
            total_points = len(question_results)
            points_earned = sum(result["points_awarded"] for result in question_results)
            percentage = (points_earned / total_points * 100) if total_points > 0 else 0
            
            # Update overall score
            data["quiz_results"]["overall_score"].update({
                "points_earned": points_earned,
                "total_points": total_points,
                "percentage": percentage,
                "grade": self._calculate_grade(percentage)
            })
            
            # Calculate performance by difficulty and topic
            data["quiz_results"]["performance_by_difficulty"] = self._calculate_difficulty_performance(
                question_results, quiz_data
            )
            data["quiz_results"]["performance_by_topic"] = self._calculate_topic_performance(
                question_results, quiz_data
            )
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {"error": f"Failed to parse evaluation response: {e}"}
        except Exception as e:
            print(f"Evaluation parsing error: {e}")
            return {"error": f"Failed to parse evaluation: {e}"}
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage"""
        if percentage >= 90: return "A"
        elif percentage >= 80: return "B"
        elif percentage >= 70: return "C"
        elif percentage >= 60: return "D"
        else: return "F"
    
    def _calculate_difficulty_performance(self, question_results: List[Dict], 
                                          quiz_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Calculate performance by difficulty level"""
        questions = quiz_data.get('quiz', {}).get('questions', quiz_data.get('questions', []))
        difficulty_stats = {"Easy": {"correct": 0, "total": 0}, 
                           "Medium": {"correct": 0, "total": 0}, 
                           "Hard": {"correct": 0, "total": 0}}
        
        for result in question_results:
            q_id = result["question_id"]
            question = next((q for q in questions if q.get('id') == q_id), None)
            if question:
                difficulty = question.get('difficulty', 'Medium')
                if difficulty in difficulty_stats:
                    difficulty_stats[difficulty]["total"] += 1
                    if result["is_correct"]:
                        difficulty_stats[difficulty]["correct"] += 1
        
        return difficulty_stats
    
    def _calculate_topic_performance(self, question_results: List[Dict], 
                                     quiz_data: Dict[str, Any]) -> List[Dict]:
        """Calculate performance by topic"""
        questions = quiz_data.get('quiz', {}).get('questions', quiz_data.get('questions', []))
        topic_stats = {}
        
        for result in question_results:
            q_id = result["question_id"]
            question = next((q for q in questions if q.get('id') == q_id), None)
            if question:
                topic = question.get('topic', 'Unknown')
                if topic not in topic_stats:
                    topic_stats[topic] = {"questions_answered": 0, "correct_answers": 0}
                
                topic_stats[topic]["questions_answered"] += 1
                if result["is_correct"]:
                    topic_stats[topic]["correct_answers"] += 1
        
        return [
            {
                "topic": topic,
                "questions_answered": stats["questions_answered"],
                "correct_answers": stats["correct_answers"],
                "percentage": (stats["correct_answers"] / stats["questions_answered"] * 100) 
                             if stats["questions_answered"] > 0 else 0
            }
            for topic, stats in topic_stats.items()
        ]
