import { createRouter, createWebHistory } from 'vue-router'
import BasicLayout from '@/views/layout/BasicLayout.vue'
import { addDynamicRoutes, hasPermission } from '@/utils/routerUtils'

// 基础路由（无需权限）
export const constantRoutes = [
  {
    path: '/',
    redirect: '/login',
    meta: { requiresAuth: false },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginPage.vue'),
    meta: {
      title: '用户登录',
      requiresAuth: false,
      hideLayout: true,
    },
  },
]

// 动态路由（基于操作权限控制）
export const dynamicRoutes = [
  {
    path: '/',
    component: BasicLayout,
    name: 'LayoutRoot',
    redirect: '/overview',
    meta: { requiresAuth: true },
    children: [
      // 总览
      {
        path: 'overview',
        component: () => import('@/views/overview/BigScreen.vue'),
        meta: {
          title: '总览',
          hideSidebar: true,
          permits: ['attackResult:list'],
        },
      },
      {
        path: 'attack',
        redirect: '/attack/AttackScore',
        meta: {
          title: '攻击成绩',
          permits: ['attackResult:list', 'appeal:list'],
          requiresAuth: true,
        },
        children: [
          {
            path: '/attack/AttackScore',
            component: () => import('@/views/attack/AttackScore.vue'),
            meta: {
              title: '攻击成绩与成果',
              hideSidebar: true,
              permits: ['attackResult:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/attack/AppealManagement',
            component: () => import('@/views/attack/AppealManagement.vue'),
            meta: {
              title: '成绩申诉',
              hideSidebar: true,
              permits: ['appeal:list'],
              requiresAuth: true,
            },
          },
        ],
      },
      {
        path: '/attack/AttackRequest',
        component: () => import('@/views/attack/AttackRequest.vue'),
        meta: {
          title: '攻击申请',
          hideSidebar: true,
          permits: ['attackRequest:list'],
          requiresAuth: true,
        },
      },
      {
        path: '/asset/AssetManagement',
        component: () => import('@/views/asset/AssetManagement.vue'),
        meta: {
          title: '资源管理',
          hideSidebar: true,
          permits: ['asset:list', 'attackAsset:list'],
          requiresAuth: true,
        },
      },
      {
        path: '/team/TeamManagement',
        component: () => import('@/views/team/TeamManagement.vue'),
        meta: {
          title: '队伍管理',
          hideSidebar: true,
          permits: ['team:list'],
          requiresAuth: true,
        },
      },
      {
        path: 'project',
        redirect: '/project/ProjectManagement',
        meta: {
          title: '项目管理',
          permits: ['project:list', 'projectMaterial:list'],
          requiresAuth: true,
        },
        children: [
          {
            path: '/project/ProjectManagement',
            component: () => import('@/views/project/ProjectManagement.vue'),
            meta: {
              title: '项目管理',
              hideSidebar: true,
              permits: ['project:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/project/ProjectMaterialManagement',
            component: () => import('@/views/project/ProjectMaterialManagement.vue'),
            meta: {
              title: '项目材料管理',
              hideSidebar: true,
              permits: ['projectMaterial:list'],
              requiresAuth: true,
            },
          },
        ],
      },
      {
        path: 'score',
        redirect: '/score/panaltyScore',
        meta: {
          title: '分数管理',
          permits: ['penaltyScore:list', 'scoringRule:list', 'scoringItem:list'],
          requiresAuth: true,
        },
        children: [
          {
            path: '/score/panaltyScore',
            component: () => import('@/views/score/panaltyScore.vue'),
            meta: {
              title: '扣分管理',
              hideSidebar: true,
              permits: ['penaltyScore:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/score/ScoringRuleManagement',
            component: () => import('@/views/score/ScoringRuleManagement.vue'),
            meta: {
              title: '评分规则管理',
              hideSidebar: true,
              permits: ['scoringRule:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/score/ScoringItemManagement',
            component: () => import('@/views/score/ScoringItemManagement.vue'),
            meta: {
              title: '评分项管理',
              hideSidebar: true,
              permits: ['scoringItem:list'],
              requiresAuth: true,
            },
          },
        ],
      },
      {
        path: 'proxy',
        redirect: '/proxy/ProxyManagement',
        meta: {
          title: '代理池管理',
          permits: ['proxyPool:list', 'userProxy:list'],
          requiresAuth: true,
        },
        children: [
          {
            path: '/proxy/ProxyManagement',
            component: () => import('@/views/proxy/ProxyManagement.vue'),
            meta: {
              title: '代理池资源',
              hideSidebar: true,
              permits: ['proxyPool:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/proxy/ProxyUser',
            component: () => import('@/views/proxy/ProxyUser.vue'),
            meta: {
              title: '用户代理',
              hideSidebar: true,
              permits: ['userProxy:list'],
              requiresAuth: true,
            },
          },
        ],
      },

      // 报告模块
      {
        path: 'report',
        component: () => import('@/views/report/ReportPage.vue'),
        meta: {
          title: '报告',
          hideSidebar: true,
          permits: ['report:list'],
          requiresAuth: true,
        },
      },

      // 系统管理模块
      {
        path: 'system',
        redirect: '/system/UserManagement',
        meta: {
          title: '系统管理',
          permits: ['attackResult:list'],
          requiresAuth: true,
        },
        children: [
          {
            path: '/system/UserManagement',
            component: () => import('@/views/system/UserManagement.vue'),
            meta: {
              title: '用户管理',
              hideSidebar: true,
              permits: ['attackResult:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/system/RoleManagement',
            component: () => import('@/views/system/RoleManagement.vue'),
            meta: {
              title: '角色管理',
              hideSidebar: true,
              permits: ['attackResult:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/system/MenuManagement',
            component: () => import('@/views/system/MenuManagement.vue'),
            meta: {
              title: '菜单管理',
              hideSidebar: true,
              permits: ['attackResult:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/system/AssignColumnsManagement',
            component: () => import('@/views/system/AssignColumnsManagement.vue'),
            meta: {
              title: '分配动态列',
              hideSidebar: true,
              permits: ['assignColumns:list'],
              requiresAuth: true,
            },
          },
          {
            path: '/system/PersonalCenter',
            component: () => import('@/views/system/PersonalCenter.vue'),
            meta: {
              title: '个人中心',
              hideSidebar: true,
              permits: ['attackResult:list'],
              requiresAuth: true,
            },
          },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: constantRoutes,
})

// src/router/index.js - 修复路由守卫
router.beforeEach(async (to, from, next) => {
  console.log('🚀 路由导航开始:', to.path, '来自:', from.path)
  console.log(
    '📋 当前路由列表:',
    router.getRoutes().map((r) => r.path),
  )

  // 设置网页标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 攻防演练平台`
  }

  // 公共路由(无需登录验证)
  const publicRoutes = ['/login', '/404']
  if (publicRoutes.includes(to.path) || to.name === 'NotFoundCatch') {
    console.log('✅ 公共路由，直接放行')
    if (to.path === '/') {
      next('/login')
      return
    }
    next()
    return
  }

  // 检查登录状态
  const token = localStorage.getItem('Authorization')
  const userPermitsStr = localStorage.getItem('user_permits')

  console.log('🔍 登录状态检查:', {
    hasToken: !!token,
    hasUserPermits: !!userPermitsStr,
  })

  if (!token || !userPermitsStr) {
    console.log('❌ 未登录或登录数据不完整，跳转到登录页')
    const items = ['Authorization', 'user_info', 'user_permits', 'dynamic_route_added']
    items.forEach((item) => localStorage.removeItem(item))
    next('/login')
    return
  }

  let userPermits
  try {
    userPermits = JSON.parse(userPermitsStr)
    console.log('~ 用户权限数量:', userPermits.length)
  } catch (error) {
    console.error('❌ 解析用户权限失败:', error)
    const items = ['Authorization', 'user_info', 'user_permits', 'dynamic_route_added']
    items.forEach((item) => localStorage.removeItem(item))
    next('/login')
    return
  }
  // 🔥 关键修复：忽略 iframe 内部路径的检查
  // 如果路径包含 .html 或看起来像静态资源路径，直接放行
  if (to.path.includes('.html') || to.path.includes('/big-screen/')) {
    console.log('🔧 忽略静态资源路径检查:', to.path)
    next()
    return
  }
  // 关键修复：无论标记如何，都重新检查并添加动态路由
  const isDynamicRouteAdded = localStorage.getItem('dynamic_route_added') === 'true'
  console.log('动态路由已添加标记:', isDynamicRouteAdded)

  // 检查当前路由是否存在
  const routeExists = router.getRoutes().some((r) => r.path === to.path)
  console.log('🔍 目标路由是否存在:', routeExists, to.path)

  if (!routeExists) {
    console.log('🔄 路由不存在，重新添加动态路由...')

    try {
      // 清除标记
      localStorage.removeItem('dynamic_route_added')

      // 添加动态路由
      await addDynamicRoutes(userPermits)
      localStorage.setItem('dynamic_route_added', 'true')
      console.log('✅ 动态路由添加完成')

      // 重新检查路由是否存在
      const newRouteExists = router.getRoutes().some((r) => r.path === to.path)
      console.log('🔍 重新检查目标路由是否存在:', newRouteExists, to.path)

      if (newRouteExists) {
        console.log('🔄 重新导航到目标页面:', to.fullPath)
        next(to.fullPath)
      } else {
        console.log('❌ 路由添加后仍然不存在，跳转到404')
        next('/404')
      }
    } catch (error) {
      console.error('❌ 添加动态路由失败:', error)
      next('/404')
    }
  } else {
    const routeRecord = router.getRoutes().find((r) => r.path === to.path)

    if (routeRecord && routeRecord.meta && routeRecord.meta.permits) {
      const hasAccess = hasPermission(userPermits, routeRecord)
      if (hasAccess) {
        console.log('✅ 有权限访问，放行')
        next()
      } else {
        console.log('❌ 无权限访问，跳转到404')
        next('/404')
      }
    } else {
      console.log('✅ 路由无权限要求，直接放行')
      next()
    }
  }
})
export default router
