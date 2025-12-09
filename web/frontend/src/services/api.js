import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:3001', // 백엔드 주소
})

export default api
