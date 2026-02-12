<template>
  <div class="code-highlight-container">
    <div class="code-header">
      <span class="file-name">{{ fileName }}</span>
      <div class="code-actions">
        <el-button size="small" link @click="toggleWrap">
          {{ wrapLines ? '取消换行' : '自动换行' }}
        </el-button>
        <el-button size="small" link @click="copyCode">
          <el-icon><DocumentCopy /></el-icon>复制
        </el-button>
      </div>
    </div>
    <div class="code-content" :class="{ 'wrap-lines': wrapLines }">
      <pre><code :class="languageClass" ref="codeRef">{{ code }}</code></pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { ElMessage } from 'element-plus'
import { DocumentCopy } from '@element-plus/icons-vue'

const props = defineProps({
  code: {
    type: String,
    default: '',
  },
  language: {
    type: String,
    default: 'javascript',
  },
  fileName: {
    type: String,
    default: 'proof',
  },
})

const codeRef = ref(null)
const wrapLines = ref(false)

const languageClass = ref(`language-${props.language}`)

// 高亮代码
const highlightCode = async () => {
  await nextTick()
  if (codeRef.value) {
    hljs.highlightElement(codeRef.value)
  }
}

// 复制代码
const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code)
    ElMessage.success('代码复制成功')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 切换换行
const toggleWrap = () => {
  wrapLines.value = !wrapLines.value
}

onMounted(() => {
  highlightCode()
})
</script>

<style scoped>
.code-highlight-container {
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  background: #0d1117;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.file-name {
  font-size: 12px;
  color: #c9d1d9;
}

.code-actions {
  display: flex;
  gap: 8px;
}

.code-content {
  overflow-x: auto;
  background: #0d1117;
}

.code-content.wrap-lines {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.code-content pre {
  margin: 0;
  padding: 16px;
  font-size: 12px;
  line-height: 1.45;
  color: #c9d1d9;
}

.code-content code {
  background: transparent;
  padding: 0;
}
</style>
