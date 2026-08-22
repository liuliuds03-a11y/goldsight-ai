import { createBrowserRouter } from 'react-router-dom'
import { Layout } from '@/components/layout'
import Dashboard from '@/pages/Dashboard'
import Gold from '@/pages/Gold'
import Prediction from '@/pages/Prediction'
import Report from '@/pages/Report'
import News from '@/pages/News'

/** 应用路由配置 */
export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/gold', element: <Gold /> },
      { path: '/prediction', element: <Prediction /> },
      { path: '/report', element: <Report /> },
      { path: '/news', element: <News /> },
    ],
  },
])
