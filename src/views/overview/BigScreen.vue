<template>
  <div class="big-screen-page">
    <IframePage src="index.html" base-path="/big-screen" />
  </div>
</template>

<script>
import IframePage from '@/components/IframePage.vue'

export default {
  name: 'BigScreen',
  components: {
    IframePage,
  },
  mounted() {
    console.log('🏠 BigScreen 组件已挂载')
  },
}
</script>

<style scoped>
.big-screen-page {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
