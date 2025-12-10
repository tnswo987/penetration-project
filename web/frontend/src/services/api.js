import axios from 'axios'

const api = axios.create({
  baseURL: 'http://172.30.1.32:3000/api',
})

export default api
