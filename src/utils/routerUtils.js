// src/utils/routerUtils.js
import router from '@/router'
import { dynamicRoutes } from '@/router'

/**
 * 检查是否有权限访问路由（基于操作权限）
 */
// src/utils/routerUtils.js - 添加详细调试
export function hasPermission(userPermits, route) {
  console.log('🔍 === 开始权限检查 ===')
  console.log('🔍 检查路由:', route.path)
  console.log('🔍 路由要求的权限:', route.meta?.permits)
  console.log('🔍 用户拥有的权限数量:', userPermits.length)

  if (route.meta && route.meta.permits) {
    // 确保 userPermits 是数组
    const userPermitsArray = Array.isArray(userPermits) ? userPermits : [userPermits]
    const requiredPermits = route.meta.permits

    console.log('🔍 路由要求的具体权限:', requiredPermits)

    // 检查用户权限是否包含路由所需的任意一个权限
    const hasPerm = requiredPermits.some((permit) => {
      const found = userPermitsArray.includes(permit)
      console.log(`🔍 检查权限 "${permit}": ${found}`)
      return found
    })

    console.log('🔍 最终权限检查结果:', hasPerm)
    console.log('🔍 === 权限检查结束 ===')

    return hasPerm
  }

  console.log('🔍 路由无权限要求，默认允许访问')
  console.log('🔍 === 权限检查结束 ===')
  return true
}

/**
 * 根据权限过滤路由
 */
export function filterRoutes(routes, userPermits) {
  console.log('🔍 开始过滤路由，用户权限数量:', userPermits.length)
  console.log('🔍 原始路由数量:', routes.length)

  const res = []

  routes.forEach((route) => {
    const tmp = { ...route }

    const hasPerm = hasPermission(userPermits, tmp)
    console.log(`🔍 路由 ${tmp.path} 权限检查:`, hasPerm)

    if (hasPerm) {
      if (tmp.children) {
        tmp.children = filterRoutes(tmp.children, userPermits)
        // 如果过滤后还有子路由，才保留该路由
        if (tmp.children.length > 0) {
          res.push(tmp)
          console.log(`✅ 保留路由 ${tmp.path}，子路由数量:`, tmp.children.length)
        } else {
          console.log(`❌ 过滤路由 ${tmp.path}，无有效子路由`)
        }
      } else {
        res.push(tmp)
        console.log(`✅ 保留路由 ${tmp.path}`)
      }
    } else {
      console.log(`❌ 过滤路由 ${tmp.path}，无权限`)
    }
  })

  console.log('🔍 过滤后路由数量:', res.length)
  return res
}
/**
 * 添加动态路由
 */
// src/utils/routerUtils.js - 添加更多调试信息
export async function addDynamicRoutes(userPermits) {
  console.log('🚀 开始添加动态路由，权限数量:', userPermits.length)
  console.log(
    '🔍 添加前路由列表:',
    router.getRoutes().map((r) => r.path),
  )

  try {
    // 清空现有动态路由
    resetRouter()

    // 根据权限过滤路由
    const accessedRoutes = filterRoutes(dynamicRoutes, userPermits)
    console.log('✅ 过滤后的路由数量:', accessedRoutes.length)

    if (accessedRoutes.length === 0) {
      console.error('❌ 没有找到任何可访问的路由')
      throw new Error('没有可访问的路由')
    }

    // 添加动态路由到根路径
    accessedRoutes.forEach((route) => {
      try {
        // 关键修复：确保正确添加路由
        if (route.name === 'LayoutRoot') {
          router.addRoute(route)
          console.log('✅ 添加主布局路由:', route.path)
        } else {
          // 对于其他路由，添加到 LayoutRoot 下
          router.addRoute('LayoutRoot', route)
          console.log('✅ 添加子路由:', route.path)
        }
      } catch (error) {
        console.error('❌ 添加路由失败:', route.path, error)
        throw error
      }
    })

    // 确保404路由在最后
    if (!router.hasRoute('NotFound')) {
      router.addRoute({
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/error/40-4.vue'),
      })
      console.log('✅ 添加404路由')
    }

    const finalRoutes = router.getRoutes()
    console.log('✅ 动态路由添加完成，总路由数:', finalRoutes.length)
    console.log(
      '📋 最终路由列表:',
      finalRoutes.map((r) => r.path),
    )

    return Promise.resolve()
  } catch (error) {
    console.error('❌ 添加动态路由过程中出错:', error)
    throw error
  }
}
/**
 * 重置路由（保留基础路由）
 */
export function resetRouter() {
  console.log('🔄 重置路由...')
  const currentRoutes = router.getRoutes()
  const constantRouteNames = ['Login', 'NotFound']

  // 移除所有非基础路由
  currentRoutes.forEach((route) => {
    if (route.name && !constantRouteNames.includes(route.name)) {
      try {
        router.removeRoute(route.name)
        console.log('🗑️ 移除路由:', route.name)
      } catch (error) {
        console.warn('⚠️ 移除路由失败:', route.name, error)
      }
    }
  })

  console.log('✅ 路由重置完成')
  console.log(
    '📋 重置后路由列表:',
    router.getRoutes().map((r) => r.path),
  )
}

export default {
  filterRoutes,
  hasPermission,
  addDynamicRoutes,
  resetRouter,
}
