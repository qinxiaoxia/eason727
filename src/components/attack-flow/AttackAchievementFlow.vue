<template>
  <div class="attack-achievement-flow">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button icon="Plus" @click="addStartNode" type="primary">添加起点</el-button>
          <el-button
            :icon="Connection"
            @click="toggleDrawingMode"
            :type="isDrawing ? 'danger' : 'default'"
          >
            {{ isDrawing ? '停止连线' : '手动连线' }}
          </el-button>
          <el-button icon="Delete" @click="clearGraph">清空画布</el-button>
        </el-button-group>

        <el-button-group class="view-controls">
          <el-button icon="ZoomIn" @click="zoomIn" title="放大"></el-button>
          <el-button icon="ZoomOut" @click="zoomOut" title="缩小"></el-button>
          <el-button icon="Refresh" @click="zoomToFit" title="适应画布"></el-button>
          <el-button icon="DocumentCopy" @click="saveAsImage" title="导出图片"></el-button>
        </el-button-group>
      </div>

      <div class="toolbar-right">
        <el-button icon="Download" @click="handleSaveFlow" type="success">保存流程图</el-button>
      </div>
    </div>

    <!-- 流程图区域 -->
    <div class="flow-container">
      <!-- 左侧节点面板 -->
      <div class="node-panel">
        <div class="panel-section">
          <div class="panel-header">
            <span>节点库</span>
          </div>
          <div class="panel-content">
            <div class="node-item" @click="addStartNode">
              <div class="node-icon start-node"></div>
              <span>起点节点</span>
            </div>
            <div class="node-item" @click="addAchievementNode">
              <div class="node-icon achievement-node"></div>
              <span>成果节点</span>
            </div>
            <div class="node-item" @click="addEndNode">
              <div class="node-icon end-node"></div>
              <span>结束节点</span>
            </div>
          </div>
        </div>

        <!-- 节点状态图例 -->
        <div class="panel-section">
          <div class="panel-header">
            <span>节点状态图例</span>
          </div>
          <div class="panel-content">
            <div v-for="item in statusLegend" :key="item.status" class="legend-item">
              <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
              <span class="legend-label">{{ item.label }}</span>
            </div>

            <!-- 操作说明 -->
            <div class="legend-tips">
              <div class="tip-item">
                <el-icon><InfoFilled /></el-icon>
                <span>双击成果节点，可展开"成果节点详情页"</span>
              </div>
              <div class="tip-item important">
                <el-icon><WarningFilled /></el-icon>
                <span>请注意标有红色*号的必填项全部完成填写后才可以校验通过。</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 流程图画布 -->
      <div ref="container" class="x6-graph-container"></div>

      <!-- 节点操作面板 -->
      <div v-if="selectedNode" class="node-operations-panel" :style="panelPosition">
        <div class="panel-header">
          <span>{{ getNodeDisplayName(selectedNode) }}</span>
          <el-icon class="close-icon" @click="closePanel"><Close /></el-icon>
        </div>
        <div class="panel-content">
          <el-button
            v-if="showAddChildButton"
            class="add-child-btn"
            type="primary"
            :icon="Plus"
            @click="addChildNode"
            size="small"
          >
            添加子节点
          </el-button>

          <div class="quick-edit">
            <el-input
              v-model="quickEditName"
              placeholder="节点名称"
              size="small"
              @blur="updateNodeName"
            />
            <el-select
              v-model="quickEditStatus"
              placeholder="状态"
              size="small"
              @change="updateNodeStatus"
            >
              <el-option label="未审核" value="pending" />
              <el-option label="校验通过" value="verified" />
              <el-option label="校验不通过" value="failed" />
            </el-select>
          </div>

          <div class="action-buttons">
            <el-button size="small" @click="editNodeProperties">详细配置</el-button>
            <el-button size="small" type="danger" @click="deleteNode">删除节点</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 节点配置面板 -->
    <el-drawer
      v-model="configDrawerVisible"
      title="节点配置"
      direction="rtl"
      size="1000px"
      :destroy-on-close="true"
    >
      <NodeConfigPanel
        v-if="selectedNode && configDrawerVisible"
        :node="selectedNode"
        @update="handleNodeConfigUpdate"
        @delete="handleNodeDelete"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { Graph } from '@antv/x6'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, Close, InfoFilled, WarningFilled } from '@element-plus/icons-vue'
import NodeConfigPanel from './NodeConfigPanel.vue'
import { attackAchievementApi } from '@/api/services/attack/attackScore'

// 图形实例
const graph = ref(null)
const container = ref(null)
const isDrawing = ref(false)
const configDrawerVisible = ref(false)
const selectedNode = ref(null)
const quickEditName = ref('')
const quickEditStatus = ref('pending')
const isGraphInitialized = ref(false)
// 状态图例数据
const statusLegend = [
  { status: 'verified', label: '校验通过', color: '#67c23a' },
  { status: 'failed', label: '校验不通过', color: '#f56c6c' },
  { status: 'pending', label: '未审核', color: '#e6a23c' },
  { status: 'rejected', label: '审核驳回', color: '#f56c6c' },
  { status: 'approved', label: '审核通过', color: '#67c23a' },
]

// 计算属性
const showAddChildButton = computed(() => {
  if (!selectedNode.value) return false
  const data = selectedNode.value.getData()
  return data && data.type !== 'end'
})

const panelPosition = computed(() => {
  if (!selectedNode.value) return {}
  const node = selectedNode.value
  const position = node.getPosition()
  const size = node.getSize()
  return {
    left: `${position.x + size.width + 20}px`,
    top: `${position.y + size.width - 65}px`,
  }
})

// 获取节点显示名称
const getNodeDisplayName = (node) => {
  const data = node.getData()
  return data?.achievementName || node.getAttr('label/text') || '未知节点'
}

// 初始化图形
// 初始化图形
const initGraph = () => {
  if (!container.value) return

  graph.value = new Graph({
    container: container.value,
    width: '100%',
    height: '100%',
    grid: {
      size: 10,
      visible: true,
      type: 'doubleMesh',
      args: [
        { color: '#e0e0e0', thickness: 1 },
        { color: '#d0d0d0', thickness: 1, factor: 5 },
      ],
    },
    background: {
      color: '#fafafa',
    },
    mousewheel: {
      enabled: true,
      modifiers: 'ctrl',
      minScale: 0.5,
      maxScale: 3,
    },
    connecting: {
      router: {
        name: 'manhattan',
        args: {
          startDirections: ['right'],
          endDirections: ['left'],
        },
      },
      connector: {
        name: 'rounded',
        args: { radius: 8 },
      },
      anchor: 'center',
      connectionPoint: 'boundary',
      allowBlank: false,
      snap: { radius: 20 },
      allowMulti: true,
      allowLoop: false,
      highlight: true,
      createEdge() {
        return graph.value.createEdge({
          shape: 'edge',
          attrs: {
            line: {
              stroke: '#409eff',
              strokeWidth: 2,
              strokeLinejoin: 'round',
              targetMarker: {
                name: 'block',
                size: 8,
                fill: '#409eff',
                offset: -1,
              },
            },
          },
          zIndex: 0,
        })
      },
    },
    highlighting: {
      magnetAvailable: {
        name: 'stroke',
        args: {
          attrs: {
            strokeWidth: 3,
            stroke: '#31d0c6',
          },
        },
      },
    },
  })

  initGraphEvents()
  addStartNode(false)

  // 标记图形实例已初始化
  isGraphInitialized.value = true
  console.log('✅ 图形实例初始化完成')
}

// 初始化图形事件
const initGraphEvents = () => {
  // 节点单击事件
  graph.value.on('node:click', ({ node }) => {
    selectedNode.value = node
    updateQuickEditForm()
  })

  // 节点双击事件
  graph.value.on('node:dblclick', ({ node }) => {
    selectedNode.value = node
    openConfigPanel()
    // 触发父组件的节点双击事件
    emit('node-dblclick', node.getData())
  })

  // 边连接成功事件
  graph.value.on('edge:connected', ({ edge }) => {
    const sourceCell = edge.getSourceCell()
    const targetCell = edge.getTargetCell()
    if (sourceCell && targetCell) {
      const sourceData = sourceCell.getData()
      const targetData = targetCell.getData()
      ElMessage.success(
        `成功连接: ${sourceData?.achievementName || '未知'} → ${targetData?.achievementName || '未知'}`,
      )
    }
  })

  // 边连接验证事件
  graph.value.on('edge:connect', ({ edge }) => {
    const sourceCell = edge.getSourceCell()
    const targetCell = edge.getTargetCell()
    if (sourceCell === targetCell) {
      ElMessage.warning('不允许节点自连接')
      return false
    }
    return true
  })

  // 画布点击事件
  graph.value.on('blank:click', () => {
    closePanel()
  })

  // 键盘事件
  graph.value.bindKey(['backspace', 'delete'], () => {
    if (selectedNode.value) {
      deleteNode()
    }
  })
}

// 打开配置面板
const openConfigPanel = () => {
  if (!selectedNode.value) return
  configDrawerVisible.value = true
}

// 编辑节点属性
const editNodeProperties = () => {
  openConfigPanel()
}

// 处理节点配置更新
const handleNodeConfigUpdate = async (configData) => {
  try {
    if (!selectedNode.value) return

    const nodeData = selectedNode.value.getData() || {}

    if (nodeData.id) {
      // 更新现有成果配置
      const result = await attackAchievementApi.modify({
        id: nodeData.id,
        ...configData,
      })

      // 安全地处理响应
      if (result && result.data) {
        // 更新节点数据
        const updatedData = { ...nodeData, ...configData }
        selectedNode.value.setData(updatedData)
        ElMessage.success('节点配置更新成功')
      } else {
        ElMessage.success('节点配置更新成功')
      }
    } else {
      // 创建新成果配置
      const result = await attackAchievementApi.add(configData)

      // 安全地处理响应
      if (result && result.data && result.data.id) {
        // 更新节点ID
        nodeData.id = result.data.id
        selectedNode.value.setData(nodeData)
        ElMessage.success('节点配置创建成功')
      } else {
        // 即使没有返回ID，也视为成功
        ElMessage.success('节点配置保存成功')
      }
    }

    // 更新快速编辑表单
    updateQuickEditForm()
  } catch (error) {
    console.error('保存节点配置失败:', error)
    ElMessage.error('保存节点配置失败: ' + (error.message || '未知错误'))
  }
}

// 处理节点删除
const handleNodeDelete = () => {
  if (!selectedNode.value) return

  const nodeName = getNodeDisplayName(selectedNode.value)
  ElMessageBox.confirm(`确定删除节点"${nodeName}"吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
    .then(() => {
      const edges = graph.value.getEdges()
      const edgesToRemove = edges.filter((edge) => {
        const sourceCell = edge.getSourceCell()
        const targetCell = edge.getTargetCell()
        return sourceCell === selectedNode.value || targetCell === selectedNode.value
      })

      graph.value.removeCells([selectedNode.value, ...edgesToRemove])
      ElMessage.success(`节点"${nodeName}"已删除`)
      closePanel()
    })
    .catch(() => {
      // 用户取消删除
    })
}

// 添加起点节点
const addStartNode = (shouldCenterView = true) => {
  if (!graph.value) return

  const node = graph.value.addNode({
    shape: 'rect',
    x: 200,
    y: 200,
    width: 120,
    height: 40,
    label: '渗透路径起点',
    data: {
      type: 'start',
      achievementName: '渗透路径起点',
      status: 'pending',
    },
    attrs: {
      body: {
        fill: '#409eff',
        stroke: '#409eff',
        strokeWidth: 2,
        rx: 6,
        ry: 6,
      },
      label: {
        text: '渗透路径起点',
        fill: '#fff',
        fontSize: 12, // 固定字体大小
        fontWeight: 'nromal',
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", // 固定字体族
      },
    },
    ports: {
      groups: {
        out: {
          position: 'right',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#409eff',
              strokeWidth: 2,
              fill: '#fff',
            },
          },
        },
      },
      items: [{ id: 'out-1', group: 'out' }],
    },
  })

  ElMessage.success('起点节点已添加')
  selectedNode.value = node
  updateQuickEditForm()

  if (shouldCenterView) {
    graph.value.centerContent()
  }
  return node
}

// 添加成果节点
const addAchievementNode = (position = null) => {
  if (!graph.value) return

  const x = position ? position.x : 400
  const y = position ? position.y : 200
  const achievementCount =
    graph.value.getNodes().filter((node) => {
      const data = node.getData()
      return data && data.type === 'achievement'
    }).length + 1

  const node = graph.value.addNode({
    shape: 'rect',
    x,
    y,
    width: 120,
    height: 60,
    label: `成果${achievementCount}`,
    data: {
      type: 'achievement',
      achievementName: `成果${achievementCount}`,
      status: 'pending',
      predictedScore: 0,
      actualScore: 0,
    },
    attrs: {
      body: {
        fill: '#e6a23c',
        stroke: '#e6a23c',
        strokeWidth: 2,
        rx: 6,
        ry: 6,
      },
      label: {
        text: `成果${achievementCount}`,
        fill: '#fff',
        fontSize: 12, // 固定字体大小
        fontWeight: 'nromal',
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", // 固定字体族
      },
    },
    ports: {
      groups: {
        in: {
          position: 'left',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#e6a23c',
              strokeWidth: 2,
              fill: '#fff',
            },
          },
        },
        out: {
          position: 'right',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#e6a23c',
              strokeWidth: 2,
              fill: '#fff',
            },
          },
        },
      },
      items: [
        { id: 'in-1', group: 'in' },
        { id: 'out-1', group: 'out' },
      ],
    },
  })

  ElMessage.success(`成果节点已添加: 成果${achievementCount}`)
  selectedNode.value = node
  updateQuickEditForm()
  return node
}

// 添加结束节点
const addEndNode = (position = null) => {
  if (!graph.value) return

  const x = position ? position.x : 600
  const y = position ? position.y : 200

  const node = graph.value.addNode({
    shape: 'rect',
    x,
    y,
    width: 120,
    height: 40,
    label: '结束节点',
    data: {
      type: 'end',
      achievementName: '结束节点',
      status: 'pending',
    },
    attrs: {
      body: {
        fill: '#f56c6c',
        stroke: '#f56c6c',
        strokeWidth: 2,
        rx: 6,
        ry: 6,
      },
      label: {
        fill: '#fff',
        fontSize: 12,
        fontWeight: 'bold',
      },
    },
    ports: {
      groups: {
        in: {
          position: 'left',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#f56c6c',
              strokeWidth: 2,
              fill: '#fff',
            },
          },
        },
      },
      items: [{ id: 'in-1', group: 'in' }],
    },
  })

  ElMessage.success('结束节点已添加')
  selectedNode.value = node
  updateQuickEditForm()
  return node
}

// 添加子节点
const addChildNode = () => {
  if (!graph.value || !selectedNode.value) return

  const parentNode = selectedNode.value
  const parentData = parentNode.getData()

  if (parentData && parentData.type === 'end') {
    ElMessage.warning('结束节点不能添加子节点')
    return
  }

  const parentPosition = parentNode.getPosition()
  const parentSize = parentNode.getSize()
  const childX = parentPosition.x + parentSize.width + 100
  const childY = parentPosition.y

  const childNode = addAchievementNode({ x: childX, y: childY })
  const childData = childNode.getData() || {}
  childData.parentId = parentNode.id
  childNode.setData(childData)

  // 自动连线
  graph.value.addEdge({
    shape: 'edge',
    source: { cell: parentNode, port: 'out-1' },
    target: { cell: childNode, port: 'in-1' },
    router: {
      name: 'manhattan',
      args: {
        startDirections: ['right'],
        endDirections: ['left'],
      },
    },
    connector: { name: 'rounded' },
    attrs: {
      line: {
        stroke: '#409eff',
        strokeWidth: 2,
        targetMarker: {
          name: 'block',
          size: 8,
          fill: '#409eff',
          offset: -1,
        },
      },
    },
    zIndex: 0,
  })

  ElMessage.success(`添加子节点: ${childData.achievementName}`)
  selectedNode.value = childNode
  updateQuickEditForm()
}

// 切换连线模式
const toggleDrawingMode = () => {
  isDrawing.value = !isDrawing.value
  if (graph.value) {
    graph.value.enableEdgeDragging = isDrawing.value
  }
  ElMessage.info(isDrawing.value ? '手动连线模式已开启' : '手动连线模式已关闭')
}

// 更新节点名称
const updateNodeName = () => {
  if (!selectedNode.value || !quickEditName.value.trim()) return

  selectedNode.value.setAttr('label/text', quickEditName.value)
  const data = selectedNode.value.getData() || {}
  data.achievementName = quickEditName.value
  selectedNode.value.setData(data)
  ElMessage.success('节点名称已更新')
}

// 更新节点状态
const updateNodeStatus = () => {
  if (!selectedNode.value) return

  const data = selectedNode.value.getData() || {}
  data.status = quickEditStatus.value
  selectedNode.value.setData(data)

  const colorMap = {
    pending: '#e6a23c',
    verified: '#67c23a',
    failed: '#f56c6c',
    rejected: '#f56c6c',
    approved: '#67c23a',
  }

  const color = colorMap[quickEditStatus.value] || '#e6a23c'
  selectedNode.value.attr('body/fill', color)
  selectedNode.value.attr('body/stroke', color)
  ElMessage.success('节点状态已更新')
}

// 更新快速编辑表单
const updateQuickEditForm = () => {
  if (!selectedNode.value) return
  const data = selectedNode.value.getData()
  quickEditName.value = data?.achievementName || selectedNode.value.getAttr('label/text') || ''
  quickEditStatus.value = data?.status || 'pending'
}

// 删除节点
const deleteNode = () => {
  if (!selectedNode.value) return

  const nodeName = getNodeDisplayName(selectedNode.value)
  ElMessageBox.confirm(`确定删除节点"${nodeName}"吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
    .then(() => {
      const edges = graph.value.getEdges()
      const edgesToRemove = edges.filter((edge) => {
        const sourceCell = edge.getSourceCell()
        const targetCell = edge.getTargetCell()
        return sourceCell === selectedNode.value || targetCell === selectedNode.value
      })

      graph.value.removeCells([selectedNode.value, ...edgesToRemove])
      ElMessage.success(`节点"${nodeName}"已删除`)
      closePanel()
    })
    .catch(() => {
      // 用户取消删除
    })
}

// 关闭操作面板
const closePanel = () => {
  selectedNode.value = null
}

// 清空画布
const clearGraph = () => {
  if (!graph.value) return

  ElMessageBox.confirm('确定清空整个画布吗？此操作不可撤销。', '清空确认', {
    type: 'warning',
    confirmButtonText: '确定清空',
    cancelButtonText: '取消',
  }).then(() => {
    graph.value.clearCells()
    ElMessage.success('画布已清空')
    closePanel()
  })
}

// 视图控制
const zoomIn = () => {
  graph.value.zoom(0.1)
}

const zoomOut = () => {
  graph.value.zoom(-0.1)
}

const zoomToFit = () => {
  graph.value.zoomToFit({ padding: 20 })
}

const saveAsImage = () => {
  graph.value.toPNG((dataUri) => {
    const link = document.createElement('a')
    link.download = '攻击路径流程图.png'
    link.href = dataUri
    link.click()
    ElMessage.success('图片导出成功')
  })
}

// 保存流程图数据
const handleSaveFlow = async () => {
  try {
    const flowData = getGraphData()
    console.log('保存流程图数据:', flowData)
    ElMessage.success('流程图保存成功')

    // 触发父组件保存事件
    emit('save', flowData)
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('流程图保存失败')
  }
}

// 获取图形数据
const getGraphData = () => {
  if (!graph.value) return null
  return graph.value.toJSON()
}

// 加载图形数据
const loadGraphData = (flowData) => {
  console.log('🚀 开始加载流程图数据:', flowData)

  // 等待图形实例初始化完成
  if (!isGraphInitialized.value) {
    console.warn('⏳ 图形实例尚未初始化，等待中...')
    const timer = setInterval(() => {
      if (isGraphInitialized.value) {
        clearInterval(timer)
        doLoadGraphData(flowData)
      }
    }, 100)
    return
  }

  doLoadGraphData(flowData)
}
const doLoadGraphData = (flowData) => {
  if (!graph.value || !flowData) {
    console.warn('❌ 图形实例或数据为空')
    return
  }
  try {
    graph.value.fromJSON(flowData)
    console.log('✅ 流程图数据加载成功')

    // 统一所有节点的字体样式
    const nodes = graph.value.getNodes()
    nodes.forEach((node) => {
      node.attr({
        label: {
          fontSize: 12, // 固定字体大小
          fontWeight: 'nromal',
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", // 固定字体族
        },
      })
    })

    // 检查边是否渲染正确
    const edges = graph.value.getEdges()
    console.log(
      '加载的边:',
      edges.map((e) => ({
        id: e.id,
        source: e.getSource(),
        target: e.getTarget(),
      })),
    )
  } catch (error) {
    console.error('❌ 加载流程图数据失败:', error)
  }
}
// 导出方法
const emit = defineEmits(['node-dblclick', 'save'])

// 生命周期
onMounted(() => {
  nextTick(() => {
    console.log('🔧 AttackAchievementFlow 组件已挂载')
    initGraph()
  })
})

onUnmounted(() => {
  if (graph.value) {
    graph.value.dispose()
  }
})

// 暴露方法给父组件
defineExpose({
  getGraphData,
  loadGraphData,
  clearGraph,
  addAchievementNode,
})
</script>

<style scoped lang="scss">
.attack-achievement-flow {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  padding: 10px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .toolbar-left {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .view-controls {
    margin-left: 20px;
  }
}

.flow-container {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.node-panel {
  width: 200px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.panel-section {
  border-bottom: 1px solid #e4e7ed;

  &:last-child {
    border-bottom: none;
  }
}

.panel-header {
  padding: 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}

.panel-content {
  padding: 15px;
}

.node-item {
  padding: 10px;
  margin: 5px 0;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s;

  &:hover {
    border-color: #409eff;
    background: #f0f9ff;
  }
}

.node-icon {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}

.start-node {
  background: #409eff;
}

.achievement-node {
  background: #e6a23c;
}

.end-node {
  background: #f56c6c;
}

/* 图例样式 */
.legend-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.legend-label {
  font-size: 12px;
  color: #606266;
}

/* 提示信息样式 */
.legend-tips {
  margin-top: 20px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 8px;

  &:last-child {
    margin-bottom: 0;
  }
}

.tip-item.important {
  color: #e6a23c;
  background: #fdf6ec;
  padding: 8px;
  border-radius: 4px;
  border-left: 4px solid #e6a23c;
  margin-left: -12px;
  margin-right: -12px;
}

.x6-graph-container {
  flex: 1;
}

.node-operations-panel {
  position: absolute;
  z-index: 1000;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 250px;
  animation: slideIn 0.2s ease-out;
  margin-left: 20px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.node-operations-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;

  .close-icon {
    cursor: pointer;
    color: #909399;

    &:hover {
      color: #409eff;
    }
  }
}

.node-operations-panel .panel-content {
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.add-child-btn,
.edit-properties-btn {
  width: 100%;
}

.quick-edit {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;

  .el-button {
    flex: 1;
  }
}
</style>
