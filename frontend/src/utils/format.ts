/**
 * GoldSight AI V3.0 - 通用格式化工具函数
 *
 * 统一各页面重复的格式化逻辑。
 */

/** 格式化数字，保留指定小数位，null/undefined 返回 '--' */
export function formatNumber(
  value: number | null | undefined,
  decimals = 2,
): string {
  if (value == null || isNaN(value)) return '--'
  return value.toFixed(decimals)
}

/** 获取涨跌颜色类名后缀 */
export function changeClass(
  value: number | null | undefined,
): string {
  if (value == null) return 'neutral'
  return value >= 0 ? 'up' : 'down'
}

/** 获取涨跌符号前缀（正数加 +） */
export function changeSign(
  value: number | null | undefined,
): string {
  if (value == null) return ''
  return value >= 0 ? '+' : ''
}

/** 格式化时间差为人类可读字符串 */
export function timeAgo(dateStr: string): string {
  if (!dateStr) return '--'
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then

  if (diff < 0) return '刚刚'
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  if (diff < 604_800_000) return `${Math.floor(diff / 86_400_000)} 天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
