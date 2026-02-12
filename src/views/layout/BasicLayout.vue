<template>
  <div class="app-container">
    <div class="full-width-navbar">
      <div class="top-navbar">
        <div class="nav-content">
          <div class="logo-container">
            <img src="@/assets/images/资产前哨logo.png" alt="中国体育彩票" class="logo-image" />
          </div>

          <el-menu
            mode="horizontal"
            class="main-nav"
            :default-active="activeTopMenu"
            @select="handleMainMenuSelect"
          >
            <el-menu-item v-for="item in visibleTopMenuItems" :key="item.index" :index="item.index">
              {{ item.title }}
            </el-menu-item>
          </el-menu>

          <div class="right-area">
            <UserMenu />
          </div>
        </div>
      </div>

      <div class="sub-navbar" v-if="showSubNav && hasSubNavPermission">
        <div class="nav-content">
          <el-menu mode="horizontal" :default-active="currentSubPath" @select="handleSubMenuSelect">
            <el-menu-item v-for="item in accessibleSubNavItems" :key="item.path" :index="item.path">
              {{ item.meta.title }}
            </el-menu-item>
          </el-menu>
        </div>
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="content-container">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import UserMenu from '@/components/UserMenu.vue'
import { getUserPermits } from '@/utils/auth'

const router = useRouter()
const route = useRoute()

// 修复权限检查函数 - 改为基于操作权限
const hasPermission = (requiredPermits) => {
  const userPermits = getUserPermits()
  console.log('🔍 菜单权限检查:', {
    required: requiredPermits,
    userHas: userPermits,
  })

  // 确保 userPermits 是数组
  const userPermitsArray = Array.isArray(userPermits) ? userPermits : [userPermits]

  // 检查用户权限是否包含所需的任意一个权限
  const hasPerm = requiredPermits.some((permit) => userPermitsArray.includes(permit))
  console.log('✅ 权限检查结果:', hasPerm)

  return hasPerm
}

// 所有顶部菜单项定义 - 改为基于操作权限
const allTopMenuItems = [
  {
    index: 'overview',
    title: '总览',
    permits: ['attackResult:list'],
  },
  {
    index: 'attack',
    title: '攻击成绩',
    permits: ['attackResult:list'],
  },
  {
    index: 'attackRequest',
    title: '攻击申请',
    permits: ['attackRequest:list'],
  },
  {
    index: 'asset',
    title: '资源管理',
    permits: ['asset:list'],
  },
  {
    index: 'teamManagement',
    title: '队伍管理',
    permits: ['team:list'],
  },
  {
    index: 'project',
    title: '项目管理',
    permits: ['project:list'],
  },
  {
    index: 'score',
    title: '分数管理',
    permits: ['penaltyScore:list'],
  },
  {
    index: 'proxy',
    title: '代理池管理',
    permits: ['proxyPool:list'],
  },
  {
    index: 'report',
    title: '报告',
    permits: ['report:list'],
  },
  {
    index: 'system',
    title: '系统管理',
    permits: ['attackResult:list'],
  },
]

// 计算当前用户可见的顶部菜单项
const visibleTopMenuItems = computed(() => {
  console.log('🔍 计算可见菜单项，用户权限:', getUserPermits())

  const visibleItems = allTopMenuItems.filter((item) => {
    const hasPerm = hasPermission(item.permits)
    console.log(`📋 菜单 "${item.title}" 权限检查:`, hasPerm)
    return hasPerm
  })

  console.log(
    '✅ 最终可见菜单项:',
    visibleItems.map((item) => item.title),
  )
  return visibleItems
})

// 获取当前激活的一级菜单
const activeTopMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/overview')) return 'overview'
  if (path.startsWith('/attack')) return 'attack'
  if (path.startsWith('/attackRequest')) return 'attackRequest'
  if (path.startsWith('/asset')) return 'asset'
  if (path.startsWith('/score')) return 'score'
  if (path.startsWith('/project')) return 'project'
  if (path.startsWith('/teamManagement')) return 'teamManagement'
  if (path.startsWith('/proxy')) return 'proxy'
  if (path.startsWith('/report')) return 'report'
  if (path.startsWith('/system')) return 'system'
  return 'overview'
})

// 获取有权限的二级导航项
const accessibleSubNavItems = computed(() => {
  const currentPath = route.path
  if (
    currentPath === '/overview' ||
    currentPath.startsWith('/report') ||
    currentPath.startsWith('/attackRequest') ||
    currentPath.startsWith('/teamManagement')
  ) {
    return []
  }

  // 获取当前激活的一级菜单对应的路由
  const mainRoute = router
    .getRoutes()
    .find((r) => r.path === `/${activeTopMenu.value}` && r.children)

  if (mainRoute && mainRoute.children) {
    return mainRoute.children
      .filter((child) => {
        // 过滤条件：有标题、不是重定向路由、有访问权限
        const hasTitle = child.meta?.title
        const isRedirect = child.redirect

        // 检查子路由的权限
        const childPermits = child.meta?.permits || []
        const hasAccess = hasPermission(childPermits)

        return hasTitle && !isRedirect && hasAccess
      })
      .map((child) => ({
        path: child.path,
        meta: child.meta,
      }))
  }

  return []
})

// 是否有二级导航权限
const hasSubNavPermission = computed(() => {
  return accessibleSubNavItems.value.length > 0
})

// 是否显示二级导航
const showSubNav = computed(() => {
  return accessibleSubNavItems.value.length > 0
})

// 当前子路径
const currentSubPath = computed(() => route.path)

// 主导航点击
const handleMainMenuSelect = (index) => {
  const routes = {
    overview: '/overview',
    attack: '/attack/AttackScore',
    attackRequest: '/attack/AttackRequest',
    asset: '/asset/AssetManagement',
    score: '/score/panaltyScore',
    teamManagement: '/team/TeamManagement',
    proxy: '/proxy/ProxyManagement',
    project: '/project/ProjectManagement',
    report: '/report',
    system: '/system/UserManagement',
  }

  const targetPath = routes[index]
  if (targetPath) {
    router.push(targetPath)
  }
}

// 二级导航点击
const handleSubMenuSelect = (path) => {
  console.log('二级导航:', path)
  router.push(path)
}

// 维护菜单样式函数
const maintainMenuStyles = () => {
  setTimeout(() => {
    const menus = document.querySelectorAll('.el-menu')
    menus.forEach((menu) => {
      if (menu.classList.contains('el-menu-horizontal')) {
        menu.classList.add('el-menu--horizontal')
      }
    })
  }, 100)
}

onMounted(() => {
  console.log('🏠 Layout 加载完成')
  console.log('👤 当前用户权限:', getUserPermits())
  maintainMenuStyles()
})

// 添加路由监听
watch(
  () => route.path,
  async () => {
    await nextTick()
    maintainMenuStyles()
  },
)
</script>

<style scoped lang="scss">
.app-container {
  display: flex;
  flex-direction: column;
  height: auto;
  overflow: hidden;
}

/* 全屏宽度导航栏容器 */
.full-width-navbar {
  width: 100%;
  position: relative;
  z-index: 10;
  margin: 0;
  padding: 0;
  background: #19222f;
}

/* 顶部主导航栏 */
.top-navbar {
  width: 100%;
  height: 60px;
  background: #b4b4b4;
  box-shadow: 0 1px 3px rgba(0, 21, 41, 0.08);
  margin: 0 auto;
  background: #19222f;

  .nav-content {
    display: flex;
    align-items: center;
    height: 100%;
    width: 100%;
    margin: 0 auto;
    padding: 0 20px;
    box-sizing: border-box;
    background: #19222f;
  }

  .logo-container {
    width: 140px;
    height: 45px;
    margin-right: 40px;
    flex-shrink: 0;

    .logo-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  .main-nav {
    flex: 1;
    background: #19222f;
    border-bottom: none;

    :deep(.el-menu--horizontal) {
      height: 60px;
      line-height: 60px;
      border-bottom: none;
      display: flex;
      flex-wrap: nowrap;
    }

    :deep(.el-menu-item) {
      height: 60px;
      line-height: 60px;
      font-size: 1.05rem;
      font-weight: 500;
      padding: 0 16px;
      margin: 0 2px;
      min-width: 80px;
      flex-shrink: 0;
    }

    /* 隐藏更多按钮 */
    :deep(.el-menu--horizontal > .el-menu-item.is-more) {
      display: none !important;
    }
  }

  .right-area {
    display: flex;
    align-items: center;
    margin-left: auto;
    flex-shrink: 0;

    .search-input {
      width: 200px;
      margin-right: 20px;
    }

    .user-info {
      display: flex;
      align-items: center;
      cursor: pointer;

      .user-name {
        margin-left: 8px;
      }
    }
  }
}

.top-navbar .el-menu--horizontal {
  --el-menu-text-color: #d2d2d2;
  --el-menu-active-color: #427ff9;
  --el-menu-hover-text-color: #19222f;
}

/* 二级导航栏 */
.sub-navbar {
  width: 100%;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  box-sizing: border-box;
  margin: 0 auto;
  padding: 0;

  .nav-content {
    max-width: none;
    margin: 0 auto;
    padding: 0 20px;
  }

  .el-menu {
    height: 48px;
    border-bottom: none;
    margin-left: 190px;

    :deep(.el-menu-item) {
      height: 48px;
      line-height: 48px;
      font-size: 1rem;
      font-weight: 500;
      padding: 0 16px;
    }
  }
}

.sub-navbar .el-menu--horizontal {
  --el-menu-text-color: #666666;
  --el-menu-active-color: #194398;
  --el-menu-hover-text-color: #19222f;
}

/* 主体内容区 */
.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  margin-top: calc(0rem + var(--sub-nav-height, 0px));
  max-width: none;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

.sub-navbar + .main-container {
  --sub-nav-height: 48px;
}

/* 内容区 */
.content-container {
  flex: 1;
  padding: 20px;
  background-color: #f0f2f5;
  overflow: auto;
  height: calc(100vh - 60px - var(--sub-nav-height, 0px));
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .top-navbar .nav-content,
  .sub-navbar .nav-content {
    padding: 0 15px;
  }
}

@media (max-width: 992px) {
  .top-navbar {
    height: auto;
    padding: 10px 0;

    .nav-content {
      flex-wrap: wrap;
    }

    .logo-container {
      margin-right: 20px;
      margin-bottom: 10px;
    }

    .main-nav {
      order: 3;
      width: 100%;
      margin-top: 10px;
    }

    .right-area {
      margin-left: 0;
      margin-bottom: 10px;
    }
  }

  /* 平板端调整种子数据菜单 */
  .seed-data-menu {
    width: 180px;

    .menu-header {
      height: 50px;
      padding: 0 16px;

      .menu-title {
        font-size: 0.9rem;
      }
    }

    .seed-menu .el-menu-item {
      height: 40px;
      line-height: 40px;
      font-size: 0.8rem;
      margin: 2px 6px;
    }
  }

  .content-container.with-seed-menu {
    width: calc(100% - 180px);
  }
}

@media (max-width: 768px) {
  .top-navbar .search-input {
    width: 150px;
    margin-right: 10px;
  }
  .seed-data-menu {
    display: none;
  }

  .content-container.with-seed-menu {
    width: 100%;
  }
}
</style>
