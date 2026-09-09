/**
 * StatSkill AI - API Client
 * Clean REST abstraction layer connecting frontend components to FastAPI backend.
 */

const API_BASE = window.location.origin;

class ApiClient {
  constructor() {
    this.token = localStorage.getItem("statskill_token") || "";
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem("statskill_token", token);
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = options.headers || {};

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errDetail = `HTTP ${response.status} Error`;
        try {
          const errJson = await response.json();
          errDetail = errJson.detail || JSON.stringify(errJson);
        } catch (_) {}
        throw new Error(errDetail);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Request failed on ${endpoint}:`, err);
      throw err;
    }
  }

  // Auth & Profile
  async getMe() {
    return this.request("/api/auth/users/me");
  }

  async getAllUsers() {
    return this.request("/api/auth/users/all");
  }

  async switchDemo(userId) {
    const res = await this.request("/api/auth/switch-demo", {
      method: "POST",
      body: JSON.stringify({ user_id: userId })
    });
    return res;
  }

  // Competency & Roles
  async getCompetencies() {
    return this.request("/api/competencies");
  }

  async getRoles() {
    return this.request("/api/roles");
  }

  async getCompetencyGaps() {
    return this.request("/api/competency/gaps");
  }

  // Diagnostic Assessment
  async startDiagnostic(assessmentId = 1) {
    return this.request(`/api/assessment/start?assessment_id=${assessmentId}`, {
      method: "POST"
    });
  }

  async submitDiagnostic(assessmentId, answers) {
    return this.request("/api/assessment/submit", {
      method: "POST",
      body: JSON.stringify({ assessment_id: assessmentId, answers })
    });
  }

  async getDiagnosticResults(attemptId) {
    return this.request(`/api/assessment/results/${attemptId}`);
  }

  // Recommendations
  async getRecommendations() {
    return this.request("/api/recommendations");
  }

  // Documents
  async uploadDocument(formData) {
    return this.request("/api/documents/upload", {
      method: "POST",
      body: formData
    });
  }

  async getDocuments() {
    return this.request("/api/documents");
  }

  async getDocument(id) {
    return this.request(`/api/documents/${id}`);
  }

  async getDocumentChunks(id) {
    return this.request(`/api/documents/${id}/chunks`);
  }

  // AI MCQ Generator & Quiz
  async generateQuiz(documentId, options = {}) {
    return this.request(`/api/documents/${documentId}/generate-quiz`, {
      method: "POST",
      body: JSON.stringify({
        document_id: documentId,
        num_questions: options.num_questions || 5,
        difficulty: options.difficulty || "Mixed",
        competency_id: options.competency_id || null
      })
    });
  }

  async getGeneratedQuestions(documentId) {
    return this.request(`/api/documents/${documentId}/generated-questions`);
  }

  async startQuiz(documentId) {
    return this.request(`/api/quiz/start?document_id=${documentId}`, {
      method: "POST"
    });
  }

  async submitQuiz(documentId, answers) {
    return this.request("/api/quiz/submit", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, answers })
    });
  }

  async login(email, password = "") {
    const res = await this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    if (res.access_token) {
      this.setToken(res.access_token);
    }
    return res.user;
  }

  // iGOT Course Catalogue
  async getCourses(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append("search", filters.search);
    if (filters.competency_name) params.append("competency_name", filters.competency_name);
    if (filters.provider) params.append("provider", filters.provider);
    if (filters.target_level) params.append("target_level", filters.target_level);
    const queryString = params.toString() ? `?${params.toString()}` : "";
    return this.request(`/api/courses${queryString}`);
  }

  async enrollCourse(courseId) {
    return this.request(`/api/courses/${courseId}/enroll`, {
      method: "POST"
    });
  }

  // Dashboards
  async getLearnerDashboard() {
    return this.request("/api/dashboard/learner");
  }

  async getAdminDashboard() {
    return this.request("/api/dashboard/admin");
  }

  // AI Doubt Solver & Chatbot
  async askDoubt(message, options = {}) {
    return this.request("/api/chat/ask", {
      method: "POST",
      body: JSON.stringify({
        message,
        document_id: options.document_id || null,
        competency_id: options.competency_id || null
      })
    });
  }

  async getChatSuggestions() {
    return this.request("/api/chat/suggestions");
  }

  async getChatHistory() {
    return this.request("/api/chat/history");
  }

  async clearChatHistory() {
    return this.request("/api/chat/history", {
      method: "DELETE"
    });
  }

  // Certifications & Credentials
  async getCertifications() {
    return this.request("/api/certifications");
  }

  async verifyCertificate(certId) {
    return this.request(`/api/certifications/verify/${encodeURIComponent(certId)}`);
  }

  async claimCertificate(courseId) {
    return this.request(`/api/certifications/claim?course_id=${courseId}`, {
      method: "POST"
    });
  }
}

const api = new ApiClient();

