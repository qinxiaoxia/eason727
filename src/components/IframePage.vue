<template>
  <div class="iframe-container">
    <iframe ref="iframeRef" frameborder="0" class="iframe-content" @load="onIframeLoad" />
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'

export default {
  name: 'IframePage',
  props: {
    src: {
      type: String,
      required: true,
      default: 'index.html',
    },
    basePath: {
      type: String,
      default: '/big-screen',
    },
  },
  setup(props) {
    const iframeRef = ref(null)

    const getFinalSrc = () => {
      // 处理基础路径
      let base = props.basePath.startsWith('/') ? props.basePath : `/${props.basePath}`

      // 处理资源路径
      let src = props.src.startsWith('/') ? props.src.substring(1) : props.src

      // 移除末尾的斜杠
      if (base.endsWith('/')) {
        base = base.slice(0, -1)
      }

      // 构建完整路径
      let fullPath = `${base}/${src}`
      
      // 获取token并添加到URL
      try {
        const token = localStorage.getItem('Authorization')
        if (token) {
          const separator = src.includes('?') ? '&' : '?'
          fullPath = `${fullPath}${separator}token=${encodeURIComponent(token)}`
        }
      } catch (e) {
        console.warn('获取token失败:', e)
      }

      // 开发环境使用绝对路径，生产环境使用相对路径
      if (import.meta.env.DEV) {
        return `${window.location.origin}${fullPath}`
      } else {
        return fullPath
      }
    }

    const setIframeSrc = () => {
      if (!iframeRef.value) return

      const finalSrc = getFinalSrc()
      console.log('🚀 设置 iframe src:', finalSrc)
      console.log('📋 当前环境:', import.meta.env.MODE)
      console.log('📍 当前域名:', window.location.origin)

      iframeRef.value.src = finalSrc
    }

    onMounted(() => {
      console.log('🔄 IframePage 已挂载')
      console.log('📦 接收到的 props:', {
        src: props.src,
        basePath: props.basePath,
      })
      setIframeSrc()
    })

    watch(() => props.src, setIframeSrc)

    const onIframeLoad = () => {
      console.log('✅ 大屏页面加载完成')
    }

    const onIframeError = (error) => {
      console.error('❌ iframe 加载错误:', error)
    }

    return {
      iframeRef,
      onIframeLoad,
      onIframeError,
    }
  },
}
</script>

<style scoped>
.iframe-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: #000;
}

.iframe-content {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
</style>
