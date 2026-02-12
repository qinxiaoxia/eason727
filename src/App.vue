<!-- src/App.vue -->
<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  console.log('🏠 App 组件挂载完成')

  // 监听路由错误
  router.onError((error) => {
    console.error('❌ 路由错误:', error)
  })

  // 监听导航失败
  router.afterEach((to, from, failure) => {
    if (failure) {
      console.error('❌ 导航失败:', failure)
    }
  })
})
</script>
<style lang="scss">
@use '@/assets/fonts.scss';
</style>
