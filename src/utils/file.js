// src/utils/file.js
/**
 * 格式化文件大小
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化后的文件大小
 */
export const formatFileSize = (bytes) => {
  if (!bytes && bytes !== 0) return '-'
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 获取文件扩展名
 * @param {string} filename - 文件名
 * @returns {string} 文件扩展名
 */
export const getFileExtension = (filename) => {
  if (!filename) return ''
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2)
}

/**
 * 获取文件类型图标
 * @param {string} filename - 文件名
 * @returns {string} 图标类型
 */
export const getFileIconType = (filename) => {
  const ext = getFileExtension(filename).toLowerCase()
  const iconMap = {
    pdf: 'pdf',
    doc: 'word',
    docx: 'word',
    xls: 'excel',
    xlsx: 'excel',
    ppt: 'ppt',
    pptx: 'ppt',
    zip: 'zip',
    rar: 'zip',
    txt: 'txt',
    jpg: 'image',
    png: 'image',
    gif: 'image',
  }
  return iconMap[ext] || 'file'
}
