import axios from 'axios'

// Production API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for quiz generation
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log('API Request:', config.method?.toUpperCase(), config.url)
    }
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log('API Response:', response.status, response.config.url)
    }
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

// API methods
export const quizAPI = {
  // Health and subjects
  healthCheck: () => api.get('/'),
  getSubjects: () => api.get('/subjects'),

  // Quiz generation and management
  generateQuiz: (subject) => api.post('/generate-quiz', { subject }),
  getQuizStatus: (sessionId) => api.get(`/quiz-status/${sessionId}`),
  getQuiz: (sessionId) => api.get(`/quiz/${sessionId}`),

  // Quiz submission and results
  submitAnswers: (sessionId, answers, userId = null) => 
    api.post('/submit-answers', {
      quiz_id: sessionId,
      user_id: userId,
      answers
    }),

  // History and session management
  getHistory: () => api.get('/history'),
  deleteSession: (sessionId) => api.delete(`/sessions/${sessionId}`),
  
  // Results retrieval
  getResults: (sessionId) => api.get(`/results/${sessionId}`)
}

// Export with both names for compatibility
export const quizFlowAPI = quizAPI

export default api