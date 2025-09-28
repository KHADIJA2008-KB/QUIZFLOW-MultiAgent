import React, { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { Trophy, TrendingUp, BookOpen, Home, RotateCcw } from 'lucide-react'
import { quizFlowAPI } from '../utils/api'

const Results = () => {
  const { sessionId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Try to get results from navigation state first
    if (location.state?.results) {
      setResults(location.state.results)
      setLoading(false)
    } else {
      // Otherwise fetch from API
      fetchResults()
    }
  }, [sessionId, location.state])

  const fetchResults = async () => {
    try {
      const response = await quizFlowAPI.getResults(sessionId)
      setResults(response.data)
    } catch (error) {
      console.error('Error fetching results:', error)
    } finally {
      setLoading(false)
    }
  }

  const getGradeColor = (grade) => {
    const colors = {
      'A': 'text-green-600 bg-green-100',
      'B': 'text-blue-600 bg-blue-100',
      'C': 'text-yellow-600 bg-yellow-100',
      'D': 'text-orange-600 bg-orange-100',
      'F': 'text-red-600 bg-red-100'
    }
    return colors[grade] || 'text-gray-600 bg-gray-100'
  }

  const getScoreMessage = (percentage) => {
    if (percentage >= 90) return "Outstanding! You've mastered this subject! 🎉"
    if (percentage >= 80) return "Great job! You have a solid understanding! 👏"
    if (percentage >= 70) return "Good work! Keep practicing to improve! 👍"
    if (percentage >= 60) return "Not bad! Review the topics you missed. 📚"
    return "Keep studying! Practice makes perfect! 💪"
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="loading-spinner mx-auto mb-4"></div>
        <p className="text-gray-600">Loading your results...</p>
      </div>
    )
  }

  if (!results || !results.quiz_results) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-4">No Results Found</h2>
        <p className="text-gray-600 mb-6">We couldn't find results for this quiz session.</p>
        <button
          onClick={() => navigate('/')}
          className="btn-primary"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  const { quiz_results } = results
  const { overall_score, question_results, performance_by_topic, recommendations } = quiz_results

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <Trophy className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Quiz Results</h1>
        <p className="text-gray-600">
          {getScoreMessage(overall_score.percentage)}
        </p>
      </div>

      {/* Overall Score Card */}
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Your Score</p>
            <p className="text-4xl font-bold text-gray-900">
              {overall_score.points_earned}/{overall_score.total_points}
            </p>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Percentage</p>
            <p className="text-4xl font-bold text-blue-600">
              {overall_score.percentage.toFixed(1)}%
            </p>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Grade</p>
            <span className={`inline-block text-3xl font-bold px-4 py-2 rounded-lg ${getGradeColor(overall_score.grade)}`}>
              {overall_score.grade}
            </span>
          </div>
        </div>
      </div>

      {/* Performance by Topic */}
      {performance_by_topic && performance_by_topic.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            Performance by Topic
          </h2>
          
          <div className="space-y-3">
            {performance_by_topic.map((topic, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <span className="font-medium text-gray-900">{topic.topic}</span>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600">
                    {topic.correct_answers}/{topic.questions_answered}
                  </span>
                  <span className="font-bold text-blue-600">
                    {topic.percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question-by-Question Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Detailed Results</h2>
        
        <div className="space-y-4">
          {question_results.map((result, index) => (
            <div key={index} className={`border rounded-lg p-4 ${
              result.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
            }`}>
              <div className="flex items-start justify-between mb-2">
                <span className="font-medium text-gray-900">Question {index + 1}</span>
                <span className={`px-2 py-1 rounded text-sm font-medium ${
                  result.is_correct 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {result.is_correct ? 'Correct' : 'Incorrect'}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Your Answer: </span>
                  <span className="text-gray-900">{result.user_answer || 'Not answered'}</span>
                </div>
                
                {!result.is_correct && (
                  <div>
                    <span className="font-medium text-gray-700">Correct Answer: </span>
                    <span className="text-green-700 font-medium">{result.correct_answer}</span>
                  </div>
                )}
                
                {result.feedback && (
                  <div className="mt-2 p-2 bg-white rounded border">
                    <span className="font-medium text-gray-700">Feedback: </span>
                    <span className="text-gray-900">{result.feedback}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <BookOpen className="h-5 w-5 mr-2" />
            Recommendations
          </h2>
          
          <ul className="space-y-2">
            {recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span className="text-gray-700">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={() => navigate('/')}
          className="btn-primary flex items-center justify-center space-x-2"
        >
          <Home className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </button>
        
        <button
          onClick={() => navigate('/')}
          className="btn-secondary flex items-center justify-center space-x-2"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Take Another Quiz</span>
        </button>
      </div>
    </div>
  )
}

export default Results
