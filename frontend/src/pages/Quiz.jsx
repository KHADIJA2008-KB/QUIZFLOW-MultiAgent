import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Clock, CheckCircle, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react'
import { quizAPI } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'

const Quiz = () => {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  
  const [quizStatus, setQuizStatus] = useState('loading')
  const [quizData, setQuizData] = useState(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [timeRemaining, setTimeRemaining] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    checkQuizStatus()
    const interval = setInterval(checkQuizStatus, 3000) // Poll every 3 seconds
    return () => clearInterval(interval)
  }, [sessionId])

  useEffect(() => {
    if (quizData?.quiz?.quiz_metadata) {
      const estimatedMinutes = quizData.quiz.quiz_metadata.estimated_time_minutes || 20
      setTimeRemaining(estimatedMinutes * 60)
    }
  }, [quizData])

  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setTimeout(() => setTimeRemaining(timeRemaining - 1), 1000)
      return () => clearTimeout(timer)
    } else if (timeRemaining === 0) {
      handleSubmitQuiz()
    }
  }, [timeRemaining])

  const checkQuizStatus = async () => {
    try {
      const statusResponse = await quizAPI.getQuizStatus(sessionId)
      const status = statusResponse.data.status
      
      setQuizStatus(status)

      if (status === 'ready') {
        const quizResponse = await quizAPI.getQuiz(sessionId)
        setQuizData(quizResponse.data)
        console.log('Quiz loaded successfully')
      } else if (status === 'failed') {
        const errorMsg = statusResponse.data.error_message || 'Unknown error'
        setError(`Quiz generation failed: ${errorMsg}`)
      }
    } catch (error) {
      console.error('Error checking quiz status:', error)
      setError(`Failed to load quiz: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleAnswerChange = (questionId, answer) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }))
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const handleSubmitQuiz = async () => {
    setIsSubmitting(true)
    try {
      const result = await quizAPI.submitAnswers(sessionId, answers)
      navigate(`/results/${sessionId}`, { state: { results: result.data } })
    } catch (error) {
      console.error('Error submitting quiz:', error)
      alert('Failed to submit quiz. Please try again.')
      setIsSubmitting(false)
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getProgressPercentage = () => {
    if (!questions) return 0
    return Math.round(((currentQuestionIndex + 1) / questions.length) * 100)
  }

  // Loading state for quiz generation
  if (quizStatus === 'loading' || quizStatus === 'generating') {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <LoadingSpinner size="lg" message="🤖 AI Agents Creating Your Quiz..." />
        <div className="mt-6 space-y-3">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">Quiz Generation in Progress</h3>
            <div className="text-left text-sm text-blue-800 space-y-1">
              <div>📋 Quiz Topic Planner: Analyzing subject areas</div>
              <div>🧠 Quiz Maker: Generating 25 questions</div>
              <div>✅ Quiz Checker: Preparing evaluation system</div>
            </div>
          </div>
          <p className="text-gray-600">
            <strong>Estimated time:</strong> 3-4 minutes<br/>
            <em>Please keep this page open while we create your personalized quiz!</em>
          </p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || quizStatus === 'failed') {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h2>
        <p className="text-gray-600 mb-6">{error || 'Quiz generation failed.'}</p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  // Quiz not ready yet
  if (!quizData?.quiz?.questions) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <LoadingSpinner size="lg" message="Loading quiz questions..." />
      </div>
    )
  }

  const questions = quizData.quiz.questions
  const currentQuestion = questions[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex === questions.length - 1
  const currentAnswer = answers[currentQuestion.id] || ''

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">
            {quizData.quiz.quiz_metadata.subject} Quiz
          </h1>
          {timeRemaining && (
            <div className="flex items-center text-red-600">
              <Clock className="h-5 w-5 mr-2" />
              <span className="font-mono text-lg">{formatTime(timeRemaining)}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Question {currentQuestionIndex + 1} of {questions.length}</span>
          <span>{getProgressPercentage()}% Complete</span>
        </div>

        <div className="mt-2 bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="mb-4 flex gap-2">
          <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
            {currentQuestion.difficulty}
          </span>
          <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
            {currentQuestion.type.replace('_', ' ').toUpperCase()}
          </span>
        </div>

        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          {currentQuestion.question}
        </h2>

        {/* Answer Options */}
        <div className="space-y-3 mb-8">
          {currentQuestion.type === 'multiple_choice' && currentQuestion.options && (
            currentQuestion.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswerChange(currentQuestion.id, option)}
                className={`w-full p-4 text-left border rounded-lg transition-colors ${
                  currentAnswer === option
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    checked={currentAnswer === option}
                    onChange={() => {}}
                    className="mr-3"
                  />
                  <span>{option}</span>
                </div>
              </button>
            ))
          )}

          {currentQuestion.type === 'true_false' && (
            ['True', 'False'].map((option) => (
              <button
                key={option}
                onClick={() => handleAnswerChange(currentQuestion.id, option)}
                className={`w-full p-4 text-left border rounded-lg transition-colors ${
                  currentAnswer === option
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    checked={currentAnswer === option}
                    onChange={() => {}}
                    className="mr-3"
                  />
                  <span>{option}</span>
                </div>
              </button>
            ))
          )}

          {currentQuestion.type === 'short_answer' && (
            <textarea
              value={currentAnswer}
              onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
              placeholder="Enter your answer here..."
              className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
            />
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={handlePreviousQuestion}
            disabled={currentQuestionIndex === 0}
            className={`flex items-center px-4 py-2 rounded-md ${
              currentQuestionIndex === 0
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-600 text-white hover:bg-gray-700'
            }`}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Previous
          </button>

          {isLastQuestion ? (
            <button
              onClick={handleSubmitQuiz}
              disabled={isSubmitting}
              className="flex items-center px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">Submitting...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Submit Quiz
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleNextQuestion}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default Quiz