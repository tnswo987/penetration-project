import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import './assets/main.css' // 기본 생성돼 있으면 그대로 둬도 됨

const app = createApp(App)

app.use(router)

app.mount('#app')
