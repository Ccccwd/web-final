import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { useUserStore } from '@/store/modules/user'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 在挂载应用前初始化用户认证状态
const initializeApp = async () => {
  const userStore = useUserStore()
  try {
    await userStore.initializeAuth()
  } catch (error) {
    console.warn('Failed to initialize auth:', error)
  }

  app.mount('#app')
}

initializeApp()