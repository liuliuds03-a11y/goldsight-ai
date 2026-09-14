import { createHashRouter } from 'react-router-dom'
import { Layout } from '@/components/layout'
import Dashboard from '@/pages/Dashboard'
import Gold from '@/pages/Gold'
import Silver from '@/pages/Silver'
import Prediction from '@/pages/Prediction'
import Report from '@/pages/Report'
import News from '@/pages/News'

/** 应用路由配置（使用 HashRouter 兼容 GitHub Pages） */
export const router = createHashRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/gold', element: <Gold /> },
      { path: '/silver', element: <Silver /> },
      { path: '/prediction', element: <Prediction /> },
      { path: '/report', element: <Report /> },
      { path: '/news', element: <News /> },
    ],
  },
])
