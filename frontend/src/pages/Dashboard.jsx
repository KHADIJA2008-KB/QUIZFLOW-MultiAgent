import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, BookOpen, Clock, TrendingUp } from 'lucide-react'
import { quizAPI } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'

const Dashboard = () => {
  const [subjects, setSubjects] = useState([])
  const [selectedSubject, setSelectedSubject] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [recentSessions, setRecentSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load subjects
      const subjectsResponse = await quizAPI.getSubjects()
      setSubjects(subjectsResponse.data.subjects)

      // Load recent sessions
      try {
        const historyResponse = await quizAPI.getHistory()
        setRecentSessions(historyResponse.data.sessions.slice(0, 5))
      } catch (error) {
        console.log('No history available yet')
        setRecentSessions([])
      }
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartQuiz = async () => {
    if (!selectedSubject) {
      alert('Please select a subject first!')
      return
    }

    setIsGenerating(true)

    try {
      console.log('Starting quiz generation for:', selectedSubject)
      const response = await quizAPI.generateQuiz(selectedSubject)
      const sessionId = response.data.session_id
      
      console.log('Quiz generation started, session:', sessionId)
      navigate(`/quiz/${sessionId}`)
    } catch (error) {
      console.error('Error starting quiz:', error)
      alert(`Failed to start quiz: ${error.response?.data?.detail || error.message}`)
      setIsGenerating(false)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-800',
      generating: 'bg-yellow-100 text-yellow-800',
      ready: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <LoadingSpinner size="lg" message="Loading dashboard..." />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to QuizFlow
        </h1>
        <p className="text-xl text-gray-600">
          AI-powered personalized quizzes for enhanced learning
        </p>
      </div>

      {/* Quiz Generator */}
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex items-center mb-6">
          <Play className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-2xl font-semibold text-gray-900">Start New Quiz</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Subject
            </label>
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isGenerating}
            >
              <option value="">Choose a subject...</option>
              {subjects.map((subject) => (
                <option key={subject} value={subject}>
                  {subject}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleStartQuiz}
              disabled={!selectedSubject || isGenerating}
              className={`w-full px-6 py-2 rounded-md font-medium transition-colors ${
                !selectedSubject || isGenerating
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isGenerating ? (
                <span className="flex items-center justify-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">Generating...</span>
                </span>
              ) : (
                'Generate Quiz'
              )}
            </button>
          </div>
        </div>

        {selectedSubject && (
          <div className="mt-4 p-4 bg-blue-50 rounded-md">
            <div className="flex items-center text-blue-800">
              <Clock className="h-4 w-4 mr-2" />
              <span className="text-sm">
                Estimated generation time: 3-4 minutes • 25 questions
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Recent Activity */}
      {recentSessions.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="flex items-center mb-6">
            <TrendingUp className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-2xl font-semibold text-gray-900">Recent Activity</h2>
          </div>

          <div className="space-y-3">
            {recentSessions.map((session) => (
              <div
                key={session.session_id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center">
                  <BookOpen className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">{session.subject}</p>
                    <p className="text-sm text-gray-500">{formatDate(session.created_at)}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(session.status)}`}>
                  {session.status}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-4 text-center">
            <button
              onClick={() => navigate('/history')}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              View All History →
            </button>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md text-center">
          <div className="text-3xl font-bold text-blue-600">{subjects.length}</div>
          <div className="text-gray-600">Available Subjects</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md text-center">
          <div className="text-3xl font-bold text-green-600">{recentSessions.length}</div>
          <div className="text-gray-600">Quizzes Taken</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md text-center">
          <div className="text-3xl font-bold text-purple-600">25</div>
          <div className="text-gray-600">Questions per Quiz</div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
