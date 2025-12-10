import { TabBar } from 'antd-mobile'
import {
  AppOutline,
  StarOutline,
  UnorderedListOutline,
  ClockCircleOutline,
  HistogramOutline,
} from 'antd-mobile-icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import styles from './Layout.module.css'

const tabs = [
  { key: '/dashboard', title: '仪表盘', icon: <AppOutline /> },
  { key: '/protocols', title: '协议', icon: <UnorderedListOutline /> },
  { key: '/favorites', title: '收藏', icon: <StarOutline /> },
  { key: '/watchlist', title: '监控', icon: <HistogramOutline /> },
  { key: '/history', title: '历史', icon: <ClockCircleOutline /> },
]

const Layout = () => {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const activeKey = tabs.find((tab) => pathname.startsWith(tab.key))?.key ?? '/dashboard'

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <Outlet />
      </div>
      <TabBar className={styles.tabBar} safeArea activeKey={activeKey} onChange={(value) => navigate(value)}>
        {tabs.map((item) => (
          <TabBar.Item key={item.key} icon={item.icon} title={item.title} />
        ))}
      </TabBar>
    </div>
  )
}

export default Layout
