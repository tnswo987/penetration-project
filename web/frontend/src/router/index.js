import { createRouter, createWebHistory } from 'vue-router'
import ModbusLogView from '../views/ModbusLogView.vue'
import DobotSensorView from '../views/DobotSensorView.vue'
import TurtlebotMonitorView from '../views/TurtlebotMonitorView.vue'

const routes = [
  { path: '/', redirect: '/logs' },
  { path: '/logs', name: 'logs', component: ModbusLogView },
  { path: '/dobot', name: 'dobot', component: DobotSensorView },
  { path: '/turtlebot', name: 'turtlebot', component: TurtlebotMonitorView },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
