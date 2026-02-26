// 大屏数据API封装
function getToken() {
  try {
    var token = localStorage.getItem('Authorization')
    if (token) {
      return token
    }
  } catch (e) {
    console.warn('无法从localStorage获取token:', e)
  }
  var urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('token') || ''
}

function getApiBaseUrl() {
  var hostname = window.location.hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return '/api'
  }
  return '/api'
}

// 获取大屏数据（所有数据汇总在一个接口）
function fetchDashboardData() {
  var token = getToken()
  var baseUrl = getApiBaseUrl()

  console.log('请求大屏数据...')

  return fetch(baseUrl + '/dashboard/data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? token : '',
    },
  })
    .then(function(response) {
      if (!response.ok) {
        throw new Error('HTTP error! status: ' + response.status)
      }
      return response.json()
    })
    .then(function(data) {
      console.log('大屏数据:', data)
      return data
    })
    .catch(function(error) {
      console.error('API请求失败:', error)
      return null
    })
}

// 导出API
window.dashboardAPI = {
  getData: fetchDashboardData,
}
