import { describe, it, expect } from 'vitest'
import { formatNumber, changeClass, changeSign, timeAgo } from '../utils/format'

describe('formatNumber', () => {
  it('格式化为两位小数', () => {
    expect(formatNumber(3.14159)).toBe('3.14')
    expect(formatNumber(100)).toBe('100.00')
    expect(formatNumber(0)).toBe('0.00')
  })

  it('支持自定义小数位', () => {
    expect(formatNumber(3.14159, 4)).toBe('3.1416')
    expect(formatNumber(100, 0)).toBe('100')
  })

  it('null/undefined 返回 --', () => {
    expect(formatNumber(null)).toBe('--')
    expect(formatNumber(undefined)).toBe('--')
  })

  it('NaN 返回 --', () => {
    expect(formatNumber(NaN)).toBe('--')
  })

  it('负数正确处理', () => {
    expect(formatNumber(-5.5)).toBe('-5.50')
  })
})

describe('changeClass', () => {
  it('正数返回 up', () => {
    expect(changeClass(1)).toBe('up')
    expect(changeClass(0.01)).toBe('up')
  })

  it('负数返回 down', () => {
    expect(changeClass(-1)).toBe('down')
    expect(changeClass(-0.01)).toBe('down')
  })

  it('零返回 up', () => {
    expect(changeClass(0)).toBe('up')
  })

  it('null 返回 neutral', () => {
    expect(changeClass(null)).toBe('neutral')
    expect(changeClass(undefined)).toBe('neutral')
  })
})

describe('changeSign', () => {
  it('正数返回 +', () => {
    expect(changeSign(1)).toBe('+')
    expect(changeSign(0.5)).toBe('+')
  })

  it('负数返回空字符串', () => {
    expect(changeSign(-1)).toBe('')
  })

  it('null 返回空字符串', () => {
    expect(changeSign(null)).toBe('')
    expect(changeSign(undefined)).toBe('')
  })
})

describe('timeAgo', () => {
  it('空字符串返回 --', () => {
    expect(timeAgo('')).toBe('--')
  })

  it('未来时间返回 刚刚', () => {
    const future = new Date(Date.now() + 100000).toISOString()
    expect(timeAgo(future)).toBe('刚刚')
  })

  it('1 分钟内返回 刚刚', () => {
    const now = new Date().toISOString()
    expect(timeAgo(now)).toBe('刚刚')
  })

  it('30 分钟前返回 N 分钟前', () => {
    const thirtyMinAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString()
    expect(timeAgo(thirtyMinAgo)).toBe('30 分钟前')
  })

  it('2 小时前返回 N 小时前', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600 * 1000).toISOString()
    expect(timeAgo(twoHoursAgo)).toBe('2 小时前')
  })

  it('3 天前返回 N 天前', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 86400 * 1000).toISOString()
    expect(timeAgo(threeDaysAgo)).toBe('3 天前')
  })
})
