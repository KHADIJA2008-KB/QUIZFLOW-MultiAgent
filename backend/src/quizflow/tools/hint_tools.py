"""
Hint and Explanation Tools
Integrates with Wikipedia API and StackOverflow API for learning resources
"""

import os
import requests
import wikipedia
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
from bs4 import BeautifulSoup
import json
import time


class WikipediaHintTool(BaseTool):
    """Tool for fetching educational content from Wikipedia"""
    
    name: str = "Wikipedia Hint Tool"
    description: str = "Fetch relevant educational content and explanations from Wikipedia"
    
    def _run(self, topic: str, max_results: int = 3) -> Dict[str, Any]:
        """Search Wikipedia for educational content on a topic"""
        try:
            # Search for relevant pages
            search_results = wikipedia.search(topic, results=max_results)
            
            if not search_results:
                return {"error": f"No Wikipedia articles found for topic: {topic}"}
            
            articles = []
            for title in search_results[:max_results]:
                try:
                    # Get page summary
                    page = wikipedia.page(title)
                    
                    # Extract key information
                    article_data = {
                        "title": page.title,
                        "url": page.url,
                        "summary": page.summary[:500] + "..." if len(page.summary) > 500 else page.summary,
                        "sections": page.sections[:5],  # First 5 sections
                        "images": page.images[:3] if hasattr(page, 'images') else []
                    }
                    articles.append(article_data)
                    
                except wikipedia.exceptions.DisambiguationError as e:
                    # Try the first disambiguation option
                    try:
                        page = wikipedia.page(e.options[0])
                        article_data = {
                            "title": page.title,
                            "url": page.url,
                            "summary": page.summary[:500] + "..." if len(page.summary) > 500 else page.summary,
                            "sections": page.sections[:5],
                            "images": page.images[:3] if hasattr(page, 'images') else []
                        }
                        articles.append(article_data)
                    except:
                        continue
                        
                except wikipedia.exceptions.PageError:
                    continue
                except Exception as e:
                    print(f"Error fetching Wikipedia page {title}: {e}")
                    continue
            
            return {
                "topic": topic,
                "source": "Wikipedia",
                "articles": articles,
                "total_found": len(articles)
            }
            
        except Exception as e:
            return {"error": f"Wikipedia search failed: {e}"}


class StackOverflowHintTool(BaseTool):
    """Tool for fetching programming help from StackOverflow API"""
    
    name: str = "StackOverflow Hint Tool"
    description: str = "Fetch programming solutions and explanations from StackOverflow"
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.stackexchange.com/2.3"
        self.site = "stackoverflow"
    
    def _run(self, query: str, tags: Optional[List[str]] = None, 
             max_results: int = 5) -> Dict[str, Any]:
        """Search StackOverflow for programming solutions"""
        try:
            # Build search parameters
            params = {
                "order": "desc",
                "sort": "relevance",
                "intitle": query,
                "site": self.site,
                "pagesize": max_results,
                "filter": "withbody"  # Include question and answer bodies
            }
            
            if tags:
                params["tagged"] = ";".join(tags)
            
            # Make API request
            response = requests.get(f"{self.base_url}/search/advanced", params=params)
            response.raise_for_status()
            
            data = response.json()
            questions = data.get("items", [])
            
            if not questions:
                return {"error": f"No StackOverflow results found for query: {query}"}
            
            processed_questions = []
            for question in questions:
                # Get answers for each question
                answers = self._get_answers(question["question_id"])
                
                question_data = {
                    "question_id": question["question_id"],
                    "title": question["title"],
                    "url": f"https://stackoverflow.com/questions/{question['question_id']}",
                    "score": question.get("score", 0),
                    "view_count": question.get("view_count", 0),
                    "answer_count": question.get("answer_count", 0),
                    "tags": question.get("tags", []),
                    "creation_date": question.get("creation_date"),
                    "body_excerpt": self._clean_html(question.get("body", ""))[:300] + "...",
                    "accepted_answer": None,
                    "top_answers": answers[:2]  # Top 2 answers
                }
                
                # Find accepted answer
                for answer in answers:
                    if answer.get("is_accepted", False):
                        question_data["accepted_answer"] = answer
                        break
                
                processed_questions.append(question_data)
            
            return {
                "query": query,
                "tags": tags,
                "source": "StackOverflow",
                "questions": processed_questions,
                "total_found": len(processed_questions)
            }
            
        except requests.RequestException as e:
            return {"error": f"StackOverflow API request failed: {e}"}
        except Exception as e:
            return {"error": f"StackOverflow search failed: {e}"}
    
    def _get_answers(self, question_id: int, max_answers: int = 3) -> List[Dict]:
        """Get answers for a specific question"""
        try:
            params = {
                "order": "desc",
                "sort": "votes",
                "site": self.site,
                "pagesize": max_answers,
                "filter": "withbody"
            }
            
            response = requests.get(
                f"{self.base_url}/questions/{question_id}/answers", 
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            answers = data.get("items", [])
            
            processed_answers = []
            for answer in answers:
                answer_data = {
                    "answer_id": answer["answer_id"],
                    "score": answer.get("score", 0),
                    "is_accepted": answer.get("is_accepted", False),
                    "creation_date": answer.get("creation_date"),
                    "body_excerpt": self._clean_html(answer.get("body", ""))[:400] + "..."
                }
                processed_answers.append(answer_data)
            
            return processed_answers
            
        except Exception as e:
            print(f"Error fetching answers for question {question_id}: {e}")
            return []
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract plain text"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text().strip()
        except:
            return html_content


class LearningResourcesTool(BaseTool):
    """Tool that combines multiple sources to provide comprehensive learning resources"""
    
    name: str = "Learning Resources Tool"
    description: str = "Combine Wikipedia and StackOverflow resources for comprehensive learning materials"
    
    def __init__(self):
        super().__init__()
        self.wikipedia_tool = WikipediaHintTool()
        self.stackoverflow_tool = StackOverflowHintTool()
    
    def _run(self, topic: str, question_type: str = "general", 
             programming_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive learning resources for a topic"""
        
        resources = {
            "topic": topic,
            "question_type": question_type,
            "wikipedia_content": None,
            "stackoverflow_content": None,
            "learning_path": [],
            "quick_tips": [],
            "additional_resources": []
        }
        
        # Get Wikipedia content for theoretical understanding
        try:
            wiki_result = self.wikipedia_tool._run(topic, max_results=2)
            if "error" not in wiki_result:
                resources["wikipedia_content"] = wiki_result
                
                # Generate learning path from Wikipedia sections
                if wiki_result.get("articles"):
                    sections = wiki_result["articles"][0].get("sections", [])
                    resources["learning_path"] = [
                        f"Study: {section}" for section in sections[:4]
                    ]
        except Exception as e:
            print(f"Error getting Wikipedia content: {e}")
        
        # Get StackOverflow content for programming topics
        if question_type in ["coding", "programming"] or programming_tags:
            try:
                so_result = self.stackoverflow_tool._run(
                    topic, 
                    tags=programming_tags, 
                    max_results=3
                )
                if "error" not in so_result:
                    resources["stackoverflow_content"] = so_result
                    
                    # Generate quick tips from top answers
                    if so_result.get("questions"):
                        for question in so_result["questions"][:2]:
                            if question.get("accepted_answer"):
                                tip = f"Solution approach: {question['accepted_answer']['body_excerpt'][:100]}..."
                                resources["quick_tips"].append(tip)
            except Exception as e:
                print(f"Error getting StackOverflow content: {e}")
        
        # Add general learning suggestions
        resources["additional_resources"] = self._generate_learning_suggestions(topic, question_type)
        
        return resources
    
    def _generate_learning_suggestions(self, topic: str, question_type: str) -> List[str]:
        """Generate additional learning suggestions based on topic and question type"""
        suggestions = []
        
        # General suggestions
        suggestions.append(f"Practice problems related to {topic}")
        suggestions.append(f"Watch video tutorials on {topic}")
        suggestions.append(f"Read official documentation for {topic}")
        
        # Type-specific suggestions
        if question_type == "coding":
            suggestions.extend([
                "Try coding exercises on platforms like LeetCode or HackerRank",
                "Review code examples and best practices",
                "Practice debugging similar problems"
            ])
        elif question_type == "theoretical":
            suggestions.extend([
                "Create mind maps to visualize concepts",
                "Discuss the topic with peers or mentors",
                "Find real-world applications of the concept"
            ])
        
        return suggestions


class HintGeneratorTool(BaseTool):
    """Tool for generating contextual hints for quiz questions"""
    
    name: str = "Hint Generator Tool"
    description: str = "Generate progressive hints and explanations for quiz questions"
    
    def __init__(self):
        super().__init__()
        self.resources_tool = LearningResourcesTool()
    
    def _run(self, question: str, correct_answer: str, user_answer: str = "", 
             difficulty: str = "Medium", topic: str = "") -> Dict[str, Any]:
        """Generate contextual hints for a quiz question"""
        
        hints = {
            "question": question,
            "difficulty": difficulty,
            "topic": topic,
            "progressive_hints": [],
            "explanation": "",
            "learning_resources": None,
            "study_suggestions": []
        }
        
        # Generate progressive hints based on difficulty
        if difficulty == "Easy":
            hints["progressive_hints"] = [
                "Think about the basic concepts related to this topic",
                "Consider the fundamental principles involved",
                f"The answer involves understanding {topic.lower()}"
            ]
        elif difficulty == "Medium":
            hints["progressive_hints"] = [
                "Break down the problem into smaller parts",
                "Consider how different concepts relate to each other",
                "Think about practical applications of the theory",
                "Review the key characteristics or properties involved"
            ]
        else:  # Hard
            hints["progressive_hints"] = [
                "This requires deep understanding of the underlying principles",
                "Consider edge cases and advanced applications",
                "Think about how this concept integrates with other advanced topics",
                "Analyze the problem from multiple perspectives"
            ]
        
        # Add hint about the correct answer (without giving it away)
        answer_hint = self._generate_answer_hint(correct_answer, question)
        if answer_hint:
            hints["progressive_hints"].append(answer_hint)
        
        # Generate explanation
        hints["explanation"] = self._generate_explanation(question, correct_answer, difficulty)
        
        # Get learning resources
        try:
            question_type = "coding" if any(keyword in question.lower() 
                                          for keyword in ["code", "function", "algorithm", "programming"]) else "general"
            resources = self.resources_tool._run(topic, question_type)
            hints["learning_resources"] = resources
        except Exception as e:
            print(f"Error getting learning resources: {e}")
        
        # Generate study suggestions
        hints["study_suggestions"] = self._generate_study_suggestions(topic, difficulty, user_answer, correct_answer)
        
        return hints
    
    def _generate_answer_hint(self, correct_answer: str, question: str) -> str:
        """Generate a hint about the correct answer without giving it away"""
        answer_lower = correct_answer.lower()
        
        # Hint patterns based on answer type
        if answer_lower in ["true", "false"]:
            return "Consider whether the statement is always, sometimes, or never true"
        elif len(correct_answer.split()) == 1:  # Single word answer
            return f"The answer is a single term related to {question.split()[-3:]}"
        elif correct_answer.startswith(('A', 'B', 'C', 'D')) and len(correct_answer) == 1:
            return "Look for the option that best fits all parts of the question"
        else:
            return f"The answer should be {len(correct_answer.split())} words long"
    
    def _generate_explanation(self, question: str, correct_answer: str, difficulty: str) -> str:
        """Generate an explanation for the correct answer"""
        return f"""
        For this {difficulty.lower()} level question about '{question[:50]}...', 
        the correct answer is '{correct_answer}'. 
        
        This concept is important because it demonstrates fundamental principles 
        that are commonly tested and applied in real-world scenarios. 
        
        To master this topic, focus on understanding the underlying logic 
        and how it connects to broader concepts in the subject area.
        """
    
    def _generate_study_suggestions(self, topic: str, difficulty: str, 
                                    user_answer: str, correct_answer: str) -> List[str]:
        """Generate personalized study suggestions"""
        suggestions = []
        
        # Base suggestions
        suggestions.append(f"Review core concepts in {topic}")
        suggestions.append(f"Practice more {difficulty.lower()} level questions on this topic")
        
        # Personalized suggestions based on user's answer
        if user_answer and user_answer.lower() != correct_answer.lower():
            if len(user_answer) == 0:
                suggestions.append("Take time to read questions carefully before answering")
            else:
                suggestions.append("Compare your reasoning with the correct explanation")
                suggestions.append("Identify where your understanding differs from the correct approach")
        
        # Difficulty-specific suggestions
        if difficulty == "Hard":
            suggestions.append("Study advanced applications and edge cases")
            suggestions.append("Practice connecting this concept to other advanced topics")
        
        return suggestions
