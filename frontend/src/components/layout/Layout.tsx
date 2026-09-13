import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Header from './Header'
import Footer from './Footer'
import './Layout.css'

/** 应用主布局：顶部导航 + 内容区 + 页脚 + 返回顶部 */
export default function Layout() {
  const [showBackTop, setShowBackTop] = useState(false)
  const location = useLocation()

  // 监听滚动
  useEffect(() => {
    const onScroll = () => setShowBackTop(window.scrollY > 400)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // 路由切换时回到顶部
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [location.pathname])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="layout">
      <Header />
      <main className="layout__main">
        <div className="layout__content">
          <Outlet />
        </div>
      </main>
      <Footer />

      {/* 返回顶部按钮 */}
      {showBackTop && (
        <button
          className="layout__back-top"
          onClick={scrollToTop}
          title="返回顶部"
        >
          ↑
        </button>
      )}
    </div>
  )
}
