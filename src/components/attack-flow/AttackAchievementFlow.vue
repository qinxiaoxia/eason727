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
        <el-button icon="Download" @click="handleSaveFlow" type="success">导出图片</el-button>
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
              <div class="tip-item">
                <el-icon><InfoFilled /></el-icon>
                <span>点击连线可选中，按 Delete 键或点击下方按钮删除</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 重要提示单独显示 -->
        <div class="important-tip">
          <el-icon><WarningFilled /></el-icon>
          <span>请注意标有红色*号的必填项全部完成填写后才可以校验通过。</span>
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

          <div class="action-buttons">
            <el-button size="small" @click="editNodeProperties">详细配置</el-button>
            <el-button size="small" type="danger" @click="deleteNode">删除节点</el-button>
          </div>
        </div>
      </div>

      <!-- 连线操作面板 -->
      <div v-if="selectedEdge" class="edge-operations-panel" :style="edgePanelStyle">
        <div class="panel-header">
          <span>连线操作</span>
          <el-icon class="close-icon" @click="selectedEdge = null"><Close /></el-icon>
        </div>
        <div class="panel-content">
          <div class="edge-info">
            <span>{{ getEdgeDisplayName(selectedEdge) }}</span>
          </div>
          <div class="action-buttons">
            <el-button size="small" type="danger" @click="deleteEdge">删除连线</el-button>
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

const props = defineProps({
  resultId: {
    type: Number,
    default: 0,
  },
  projectId: {
    type: Number,
    default: 0,
  },
  attackTeamId: {
    type: Number,
    default: 0,
  },
  defenseTeamId: {
    type: Number,
    default: 0,
  },
})

// 图形实例
const graph = ref(null)
const container = ref(null)
const isDrawing = ref(false)
const configDrawerVisible = ref(false)
const selectedNode = ref(null)
const selectedEdge = ref(null)
const edgePanelPosition = ref({ x: 0, y: 0 })
const isLoadingData = ref(false)
const quickEditName = ref('')
const quickEditStatus = ref('pending')
const isGraphInitialized = ref(false)
// 状态图例数据
const statusLegend = [
  { status: 'pending', label: '待审核', color: '#e6a23c' },
  { status: 'approved', label: '已批准', color: '#67c23a' },
  { status: 'rejected', label: '已拒绝', color: '#f56c6c' },
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

const edgePanelStyle = computed(() => {
  return {
    left: `${edgePanelPosition.value.x}px`,
    top: `${edgePanelPosition.value.y}px`,
    transform: 'translateX(-50%)',
  }
})

// 获取节点显示名称
const getNodeDisplayName = (node) => {
  const data = node.getData()
  return data?.achievementName || node.getAttr('label/text') || '未知节点'
}

// 获取连线显示名称
const getEdgeDisplayName = (edge) => {
  const sourceCell = edge.getSourceCell()
  const targetCell = edge.getTargetCell()
  const sourceData = sourceCell?.getData()
  const targetData = targetCell?.getData()
  const sourceName = sourceData?.achievementName || sourceCell?.getAttr('label/text') || '起点'
  const targetName = targetData?.achievementName || targetCell?.getAttr('label/text') || '终点'
  return `${sourceName} → ${targetName}`
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
    if (!isLoadingData.value) {
      const nodeData = node.getData()
      // 只对成果节点显示操作面板，忽略起点和终点
      if (nodeData && nodeData.type === 'achievement') {
        selectedNode.value = node
        updateQuickEditForm()
      }
    }
  })

  // 节点双击事件
  graph.value.on('node:dblclick', ({ node }) => {
    const nodeData = node.getData()
    // 只对成果节点打开配置面板
    if (nodeData && nodeData.type === 'achievement') {
      selectedNode.value = node
      openConfigPanel()
      // 触发父组件的节点双击事件
      emit('node-dblclick', node.getData())
    }
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

  // 边点击事件 - 选中边
  graph.value.on('edge:click', ({ edge }) => {
    selectedEdge.value = edge

    const sourceData = edge.getSourceCell()?.getData()
    const targetData = edge.getTargetCell()?.getData()

    const edgePosition = edge.getBBox().getCenter()
    edgePanelPosition.value = {
      x: edgePosition.x,
      y: edgePosition.y - 60,
    }

    ElMessage.info(
      `已选中连接: ${sourceData?.achievementName || '起点'} → ${targetData?.achievementName || '终点'}`,
    )
  })

  // 画布点击事件
  graph.value.on('blank:click', () => {
    closePanel()
    selectedEdge.value = null
  })

  // 键盘事件
  graph.value.bindKey(['backspace', 'delete'], () => {
    if (selectedNode.value) {
      deleteNode()
    } else if (selectedEdge.value) {
      deleteEdge()
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

    const saveData = {
      ...configData,
      resultId: props.resultId,
      projectId: props.projectId,
      attackTeamId: props.attackTeamId,
      defenseTeamId: props.defenseTeamId,
    }

    if (nodeData.id) {
      // 更新现有成果配置
      const result = await attackAchievementApi.modify(
        {
          id: nodeData.id,
          ...saveData,
        },
        [],
      )

      // 安全地处理响应
      if (result) {
        // 更新节点数据
        const updatedData = { ...nodeData, ...saveData }
        selectedNode.value.setData(updatedData)
        ElMessage.success('节点配置更新成功')
      } else {
        ElMessage.success('节点配置更新成功')
      }
    } else {
      // 创建新成果配置
      const result = await attackAchievementApi.add(saveData, [])

      // 安全地处理响应
      if (result && result.data && result.data.id) {
        // 更新节点ID
        const updatedData = { ...nodeData, ...saveData, id: result.data.id }
        selectedNode.value.setData(updatedData)
        ElMessage.success('节点配置创建成功')
      } else {
        // 即使没有返回ID，也视为成功
        const updatedData = { ...nodeData, ...saveData }
        selectedNode.value.setData(updatedData)
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

// 删除选中的边
const deleteEdge = () => {
  if (!selectedEdge.value || !graph.value) return

  const sourceData = selectedEdge.value.getSourceCell()?.getData()
  const targetData = selectedEdge.value.getTargetCell()?.getData()
  const edgeName = `${sourceData?.achievementName || '起点'} → ${targetData?.achievementName || '终点'}`

  ElMessageBox.confirm(`确定删除连接"${edgeName}"吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
    .then(() => {
      graph.value.removeEdge(selectedEdge.value)
      ElMessage.success(`连接"${edgeName}"已删除`)
      selectedEdge.value = null
    })
    .catch(() => {
      // 用户取消删除
    })
}

// 添加起点节点
const addStartNode = (shouldCenterView = true) => {
  if (!graph.value) return

  const node = graph.value.addNode({
    shape: 'circle',
    x: 200,
    y: 200,
    width: 60,
    height: 60,
    label: '起点',
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
      },
      label: {
        text: '起点',
        fill: '#fff',
        fontSize: 12,
        fontWeight: 'nromal',
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
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
    shape: 'polygon',
    x,
    y,
    width: 100,
    height: 60,
    points: '50,0 100,30 50,60 0,30',
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
      },
      label: {
        text: `成果${achievementCount}`,
        fill: '#fff',
        fontSize: 12,
        fontWeight: 'nromal',
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      },
    },
    ports: {
      groups: {
        left: {
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
        right: {
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
        top: {
          position: 'top',
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
        bottom: {
          position: 'bottom',
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
        { id: 'left', group: 'left' },
        { id: 'right', group: 'right' },
        { id: 'top', group: 'top' },
        { id: 'bottom', group: 'bottom' },
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

  try {
    const parentNode = selectedNode.value
    const parentData = parentNode.getData()

    if (parentData && parentData.type === 'end') {
      ElMessage.warning('结束节点不能添加子节点')
      return
    }

    const parentPosition = parentNode.getPosition()
    const parentSize = parentNode.getSize()

    const childCount = parentData?.childCount || 0
    const offsetY = 80
    const childX = parentPosition.x + parentSize.width + 150
    const childY = parentPosition.y + childCount * offsetY

    parentData.childCount = childCount + 1
    parentNode.setData(parentData)

    const childNode = addAchievementNode({ x: childX, y: childY })
    const childData = childNode.getData() || {}
    childData.parentId = parentNode.id
    childNode.setData(childData)

    // 自动连线
    const edge = graph.value.addEdge({
      shape: 'edge',
      source: { cell: parentNode, port: 'right' },
      target: { cell: childNode, port: 'left' },
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

    console.log('✅ 成功创建边:', edge)
    ElMessage.success(`添加子节点: ${childData.achievementName}`)
    selectedNode.value = childNode
    updateQuickEditForm()
  } catch (error) {
    console.error('添加子节点失败:', error)
    ElMessage.error('添加子节点失败: ' + (error.message || '未知错误'))
  }
}

// 切换连线模式
const toggleDrawingMode = () => {
  isDrawing.value = !isDrawing.value
  if (graph.value) {
    graph.value.enableEdgeDragging = isDrawing.value
  }
  ElMessage.info(isDrawing.value ? '手动连线模式已开启' : '手动连线模式已关闭')
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
  if (!selectedNode.value || !graph.value) return

  const nodeName = getNodeDisplayName(selectedNode.value)
  ElMessageBox.confirm(`确定删除节点"${nodeName}"吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
    .then(() => {
      try {
        const edges = graph.value.getEdges()
        const edgesToRemove = edges.filter((edge) => {
          const sourceCell = edge.getSourceCell()
          const targetCell = edge.getTargetCell()
          return sourceCell === selectedNode.value || targetCell === selectedNode.value
        })

        const cellsToRemove = [selectedNode.value, ...edgesToRemove]
        graph.value.removeCells(cellsToRemove)
        ElMessage.success(`节点"${nodeName}"已删除`)
        closePanel()
      } catch (error) {
        console.error('删除节点失败:', error)
        ElMessage.error('删除节点失败: ' + (error.message || '未知错误'))
      }
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

// 重置画布（不带确认，用于新建成果时）
const resetGraph = () => {
  if (!graph.value) return
  graph.value.clearCells()
  addStartNode(false)
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

// 导出流程图为图片
const handleSaveFlow = async () => {
  try {
    if (!graph.value) {
      ElMessage.warning('流程图不存在')
      return
    }

    const graphView = graph.value.view
    if (!graphView) {
      ElMessage.error('无法获取画布视图')
      return
    }

    const svgElement = graphView.container.querySelector('svg')
    if (!svgElement) {
      ElMessage.error('无法获取SVG元素')
      return
    }

    ElMessage.info('正在导出，请稍候...')

    const serializer = new XMLSerializer()
    let svgString = serializer.serializeToString(svgElement)

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    const scale = 1

    const containerRect = graphView.container.getBoundingClientRect()
    const canvasWidth = containerRect.width * scale
    const canvasHeight = containerRect.height * scale

    canvas.width = canvasWidth
    canvas.height = canvasHeight

    svgString = svgString.replace('width="100%"', `width="${containerRect.width}"`)
    svgString = svgString.replace('height="100%"', `height="${containerRect.height}"`)

    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    img.onload = () => {
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)
      ctx.drawImage(img, 0, 0)

      const pngUrl = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `攻击路径流程图-${new Date().toLocaleString()}.png`
      link.href = pngUrl
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      ElMessage.success('流程图导出成功')
    }

    img.onerror = (e) => {
      console.error('图片加载失败:', e)
      ElMessage.error('图片加载失败')
    }

    img.src = url
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('流程图导出失败: ' + error.message)
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

  // 标记正在加载数据
  isLoadingData.value = true

  // 等待图形实例初始化完成
  if (!isGraphInitialized.value) {
    console.warn('⏳ 图形实例尚未初始化，等待中...')
    const timer = setInterval(() => {
      if (isGraphInitialized.value) {
        clearInterval(timer)
        doLoadGraphData(flowData)
        // 加载完成后清除选中状态
        selectedNode.value = null
        // 加载完成后重置状态
        setTimeout(() => {
          isLoadingData.value = false
        }, 500)
      }
    }, 100)
    return
  }

  doLoadGraphData(flowData)
  // 加载完成后清除选中状态
  selectedNode.value = null
  // 加载完成后重置状态
  setTimeout(() => {
    isLoadingData.value = false
  }, 500)
}
const doLoadGraphData = (flowData) => {
  if (!graph.value || !flowData) {
    console.warn('❌ 图形实例或数据为空')
    return
  }
  try {
    console.log('📝 开始加载数据到画布:', flowData)
    graph.value.fromJSON(flowData)
    console.log('✅ 流程图数据加载成功')

    // 统一所有节点的字体样式
    const nodes = graph.value.getNodes()
    console.log(`📊 加载了 ${nodes.length} 个节点`)
    nodes.forEach((node) => {
      const nodeData = node.getData()
      console.log(
        `  节点: ${node.id}, type: ${nodeData?.type}, achievementName: ${nodeData?.achievementName}`,
      )
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
    console.log(`🔗 加载了 ${edges.length} 条边`)
    edges.forEach((edge) => {
      console.log(
        `  边: ${edge.id}, source: ${edge.getSource().cell?.id}, target: ${edge.getTarget().cell?.id}`,
      )
    })
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
  resetGraph,
  addAchievementNode,
  getGraph: () => graph.value,
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
  width: 180px;
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
  padding: 10px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: bold;
  font-size: 13px;
  color: #303133;
}

.panel-content {
  padding: 10px 12px;
}

.node-item {
  padding: 8px;
  margin: 4px 0;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;

  &:hover {
    border-color: #409eff;
    background: #f0f9ff;
  }
}

.node-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.start-node {
  width: 16px;
  height: 16px;
  background: #909399;
  border-radius: 50%;
}

.achievement-node {
  width: 14px;
  height: 14px;
  background: #909399;
  transform: rotate(45deg);
}

.end-node {
  width: 18px;
  height: 14px;
  background: #909399;
  border-radius: 2px;
}

/* 图例样式 */
.legend-item {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
}

.legend-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.legend-label {
  font-size: 12px;
  color: #606266;
}

/* 提示信息样式 */
.legend-tips {
  margin-top: 10px;
  padding: 8px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 11px;
  color: #606266;
  margin-bottom: 4px;

  &:last-child {
    margin-bottom: 0;
  }

  .el-icon {
    font-size: 12px;
    margin-top: 1px;
  }
}

.tip-item.important {
  color: #e6a23c;
  background: #fdf6ec;
  padding: 6px;
  border-radius: 4px;
  border-left: 3px solid #e6a23c;
  margin-left: -8px;
  margin-right: -8px;
}

.important-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  color: #e6a23c;
  background: #fdf6ec;
  padding: 10px 12px;
  border-radius: 4px;
  border-left: 4px solid #e6a23c;
  font-size: 12px;
  line-height: 1.5;
  margin: 10px 12px;

  .el-icon {
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 1px;
  }
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

.edge-operations-panel {
  position: absolute;
  z-index: 1000;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  animation: slideIn 0.2s ease-out;
}

.edge-operations-panel .panel-header {
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

.edge-operations-panel .panel-content {
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.edge-info {
  text-align: center;
  color: #606266;
  font-size: 14px;
}
</style>
