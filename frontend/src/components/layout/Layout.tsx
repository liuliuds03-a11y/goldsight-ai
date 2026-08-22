import { Outlet } from 'react-router-dom'
import Header from './Header'
import Footer from './Footer'
import './Layout.css'

/** 应用主布局：顶部导航 + 内容区 + 页脚 */
export default function Layout() {
  return (
    <div className="layout">
      <Header />
      <main className="layout__main">
        <div className="layout__content">
          <Outlet />
        </div>
      </main>
      <Footer />
    </div>
  )
}
