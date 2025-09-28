#!/usr/bin/env python
"""
Main entry point for QuizFlow CLI operations
"""
import sys
import warnings
from datetime import datetime
from quizflow.crew import QuizflowCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the QuizFlow crew to generate a quiz for a default subject.
    """
    subject = sys.argv[1] if len(sys.argv) > 1 else "Computer Science"
    
    print(f"🎯 Generating quiz for subject: {subject}")
    
    try:
        crew_instance = QuizflowCrew()
        result = crew_instance.generate_quiz_for_subject(subject)
        print(f"✅ Quiz generation completed successfully!")
        print(f"📊 Generated {len(result.get('quiz', {}).get('questions', []))} questions")
        return result
    except Exception as e:
        print(f"❌ An error occurred while running QuizFlow: {e}")
        raise

def train():
    """
    Train the QuizFlow crew for a given number of iterations.
    """
    if len(sys.argv) < 3:
        print("Usage: train <iterations> <filename>")
        sys.exit(1)
    
    iterations = int(sys.argv[1])
    filename = sys.argv[2]
    subject = sys.argv[3] if len(sys.argv) > 3 else "Computer Science"
    
    inputs = {
        "subject": subject,
        "current_year": str(datetime.now().year)
    }
    
    try:
        crew_instance = QuizflowCrew()
        crew_instance.crew().train(n_iterations=iterations, filename=filename, inputs=inputs)
        print(f"✅ Training completed for {iterations} iterations")
    except Exception as e:
        print(f"❌ An error occurred while training QuizFlow: {e}")
        raise

def replay():
    """
    Replay the QuizFlow crew execution from a specific task.
    """
    if len(sys.argv) < 2:
        print("Usage: replay <task_id>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    try:
        crew_instance = QuizflowCrew()
        crew_instance.crew().replay(task_id=task_id)
        print(f"✅ Replay completed for task: {task_id}")
    except Exception as e:
        print(f"❌ An error occurred while replaying QuizFlow: {e}")
        raise

def test():
    """
    Test the QuizFlow crew execution and return results.
    """
    if len(sys.argv) < 3:
        print("Usage: test <iterations> <eval_llm>")
        sys.exit(1)
    
    iterations = int(sys.argv[1])
    eval_llm = sys.argv[2]
    subject = sys.argv[3] if len(sys.argv) > 3 else "Computer Science"
    
    inputs = {
        "subject": subject,
        "current_year": str(datetime.now().year)
    }
    
    try:
        crew_instance = QuizflowCrew()
        crew_instance.crew().test(n_iterations=iterations, eval_llm=eval_llm, inputs=inputs)
        print(f"✅ Testing completed for {iterations} iterations")
    except Exception as e:
        print(f"❌ An error occurred while testing QuizFlow: {e}")
        raise

if __name__ == "__main__":
    run()
