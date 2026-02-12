import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import dayjs from 'dayjs'
import * as ElIcons from '@element-plus/icons-vue'
import './styles/element-variables.css'
import '@/assets/fonts.scss'

router
  .isReady()
  .then(() => {
    console.log('✅ 路由初始化完成')
  })
  .catch((error) => {
    console.error('❌ 路由初始化失败:', error)
  })

console.log('Router configuration:', router.getRoutes())
const pinia = createPinia()
const app = createApp(App)
app.config.globalProperties.$dayjs = dayjs
for (const [key, component] of Object.entries(ElIcons)) {
  app.component(key, component)
}
app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')
console.log('App mounted successfully')
router.afterEach(() => {
  console.log(
    '🔍 当前路由列表:',
    router.getRoutes().map((r) => r.path),
  )
})
