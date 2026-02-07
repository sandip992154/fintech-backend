import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.message);
    
    // Handle specific error cases
    if (error.response?.status === 404) {
      console.warn('🔍 Resource not found');
    } else if (error.response?.status >= 500) {
      console.error('🚨 Server error occurred');
    } else if (error.code === 'ECONNABORTED') {
      console.error('⏰ Request timeout');
    } else if (!error.response) {
      console.error('🌐 Network error - check your connection');
    }
    
    return Promise.reject(error);
  }
);

// API endpoints
export const apiEndpoints = {
  // Products
  getLatestPopular: (params = {}) => api.get('/products/latest-popular', { params }),
  getHotDeals: (params = {}) => api.get('/products/hot-deals', { params }),
  getBestSelling: (params = {}) => api.get('/products/best-selling', { params }),
  getProductDetail: (id) => api.get(`/product/${id}`),
  getProductById: (id) => api.get(`/products/${id}`),
  searchProducts: (params = {}) => api.get('/products/search', { params }),
  compareProducts: (productIds) => api.post('/products/compare', productIds),
  
  // Comparison - Optimized single query endpoints
  getComparisonProducts: (productIds) => api.get('/comparison/batch', { 
    params: { product_ids: productIds }
  }),
  getSuggestedComparisons: (params = {}) => api.get('/comparison/suggest', { params }),
  getPriceAnalysis: (productId) => api.get(`/comparison/price-analysis/${productId}`),
  
  // Categories & Filters
  getCategories: () => api.get('/categories'),
  getBrands: (params = {}) => api.get('/brands', { params }),
  getFilterOptions: (category) => api.get('/filter-options', { params: { category } }),
  
  // Contact
  submitContact: (data) => api.post('/contact-us', data),
  sendContactMessage: (data) => api.post('/contact', data)
};

export const apiService = apiEndpoints;

export default api;