import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, BookOpen, Eye, Trash2, Filter } from 'lucide-react'
import { quizFlowAPI } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'

const History = () => {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, completed, generating, failed
  const navigate = useNavigate()

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const response = await quizFlowAPI.getHistory()
      setSessions(response.data.sessions)
    } catch (error) {
      console.error('Error loading history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteSession = async (sessionId) => {
    if (!confirm('Are you sure you want to delete this quiz session?')) {
      return
    }

    try {
      await quizFlowAPI.deleteSession(sessionId)
      setSessions(sessions.filter(session => session.session_id !== sessionId))
    } catch (error) {
      console.error('Error deleting session:', error)
      alert('Failed to delete session. Please try again.')
    }
  }

  const handleViewResults = (sessionId) => {
    navigate(`/results/${sessionId}`)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'bg-green-100 text-green-800',
      generating: 'bg-yellow-100 text-yellow-800',
      ready: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800'
    }

    const icons = {
      completed: '✓',
      generating: '⏳',
      ready: '⚡',
      failed: '✗'
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badges[status] || 'bg-gray-100 text-gray-800'}`}>
        <span className="mr-1">{icons[status] || '?'}</span>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const filteredSessions = sessions.filter(session => {
    if (filter === 'all') return true
    return session.status === filter
  })

  const getFilterCounts = () => {
    const counts = sessions.reduce((acc, session) => {
      acc[session.status] = (acc[session.status] || 0) + 1
      return acc
    }, {})
    counts.all = sessions.length
    return counts
  }

  const filterCounts = getFilterCounts()

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto text-center py-12">
        <LoadingSpinner size="lg" message="Loading quiz history..." />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Quiz History</h1>
        <p className="text-gray-600">View and manage your past quiz sessions</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center space-x-2 mb-4">
          <Filter className="h-5 w-5 text-gray-500" />
          <span className="font-medium text-gray-700">Filter by status:</span>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {[
            { key: 'all', label: 'All' },
            { key: 'completed', label: 'Completed' },
            { key: 'ready', label: 'Ready' },
            { key: 'generating', label: 'Generating' },
            { key: 'failed', label: 'Failed' }
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                filter === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {label} ({filterCounts[key] || 0})
            </button>
          ))}
        </div>
      </div>

      {/* Sessions List */}
      {filteredSessions.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            {filter === 'all' ? 'No quiz sessions yet' : `No ${filter} sessions`}
          </h3>
          <p className="text-gray-600 mb-6">
            {filter === 'all' 
              ? 'Start your first quiz to see it here!' 
              : `Try changing the filter to see more sessions.`
            }
          </p>
          <button
            onClick={() => navigate('/')}
            className="btn-primary"
          >
            Start New Quiz
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subject
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date & Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSessions.map((session) => (
                  <tr key={session.session_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <BookOpen className="h-5 w-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {session.subject}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {session.session_id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(session.status)}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-900">
                        <Clock className="h-4 w-4 text-gray-400 mr-2" />
                        {formatDate(session.created_at)}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-3">
                        {session.status === 'completed' && (
                          <button
                            onClick={() => handleViewResults(session.session_id)}
                            className="text-blue-600 hover:text-blue-900 flex items-center space-x-1"
                          >
                            <Eye className="h-4 w-4" />
                            <span>View Results</span>
                          </button>
                        )}
                        
                        {session.status === 'ready' && (
                          <button
                            onClick={() => navigate(`/quiz/${session.session_id}`)}
                            className="text-green-600 hover:text-green-900 flex items-center space-x-1"
                          >
                            <BookOpen className="h-4 w-4" />
                            <span>Take Quiz</span>
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDeleteSession(session.session_id)}
                          className="text-red-600 hover:text-red-900 flex items-center space-x-1"
                        >
                          <Trash2 className="h-4 w-4" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Stats Summary */}
      {sessions.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{sessions.length}</p>
              <p className="text-sm text-gray-600">Total Sessions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{filterCounts.completed || 0}</p>
              <p className="text-sm text-gray-600">Completed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">{filterCounts.generating || 0}</p>
              <p className="text-sm text-gray-600">In Progress</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{filterCounts.failed || 0}</p>
              <p className="text-sm text-gray-600">Failed</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default History
