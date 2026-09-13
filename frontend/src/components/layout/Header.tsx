import { Link, useLocation } from 'react-router-dom'
import './Header.css'

/** 导航菜单项 */
const NAV_ITEMS = [
  { path: '/', label: '总览' },
  { path: '/gold', label: '黄金' },
  { path: '/silver', label: '白银' },
  { path: '/prediction', label: '预测' },
  { path: '/report', label: '报告' },
  { path: '/news', label: '新闻' },
]

export default function Header() {
  const location = useLocation()

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="header__logo">
          <span className="header__logo-icon">Au</span>
          <span className="header__logo-text">GoldSight AI</span>
        </Link>

        <nav className="header__nav">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`header__nav-item ${
                location.pathname === item.path ? 'header__nav-item--active' : ''
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="header__actions">
          <span className="header__status">GoldSight V3.0</span>
        </div>
      </div>
    </header>
  )
}
