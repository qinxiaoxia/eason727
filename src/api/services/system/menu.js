// @/api/services/system/menu.js
import request from '@/utils/request'

export default {
  // 获取菜单分页列表
  getPageList(params) {
    return request({
      url: '/sysMenu/page',
      method: 'POST',
      data: params,
    })
  },

  // 新增菜单
  addMenu(data) {
    return request({
      url: '/sysMenu/add',
      method: 'POST',
      data,
    })
  },

  // 编辑菜单
  editMenu(data) {
    return request({
      url: '/sysMenu/edit',
      method: 'POST',
      data,
    })
  },

  // 删除菜单
  removeMenu(id) {
    return request({
      url: `/sysMenu/remove/${id}`,
      method: 'POST',
    })
  },

  // 批量删除菜单
  batchRemoveMenus(ids) {
    return request({
      url: '/sysMenu/removes',
      method: 'POST',
      data: ids,
    })
  },

  // 根据菜单ids查询选中菜单树结构
  getMenuTreeBySelectedIds(params) {
    return request({
      url: '/sysMenu/xmSelect',
      method: 'POST',
      data: params,
    })
  },

  // 获取完整的菜单树（如果没有单独接口，可以通过分页数据构建）
  getFullMenuTree(params) {
    return request({
      url: '/sysMenu/page',
      method: 'POST',
      data: { ...params, limit: 1000 }, // 获取所有菜单
    }).then((response) => {
      // 将扁平数据转换为树形结构
      const flatMenus = response.data || []
      return buildMenuTree(flatMenus)
    })
  },
}

// 构建菜单树形结构的工具函数
function buildMenuTree(flatMenus) {
  if (!flatMenus || flatMenus.length === 0) {
    return []
  }

  const menuMap = {}
  const tree = []

  // 创建映射
  flatMenus.forEach((menu) => {
    menuMap[menu.id] = { ...menu, children: [] }
  })

  // 构建树形结构
  flatMenus.forEach((menu) => {
    if (menu.parentId && menuMap[menu.parentId]) {
      menuMap[menu.parentId].children.push(menuMap[menu.id])
    } else {
      tree.push(menuMap[menu.id])
    }
  })

  return tree
}
