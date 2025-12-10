import { useAuthStore } from '@/store/auth'
import { selectTheme, useUIStore } from '@/store/ui'
import { Button, List, Switch, Tag } from 'antd-mobile'
import styles from './Page.module.css'

const Settings = () => {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const theme = useUIStore(selectTheme)
  const setTheme = useUIStore((state) => state.setTheme)

  return (
    <div className={styles.page}>
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>账户信息</div>
          <div className={styles.sectionSubtitle}>来自 Telegram</div>
        </div>
        <List className={styles.list}>
          <List.Item extra={user?.username ?? '未知'}>用户名</List.Item>
          <List.Item extra={user?.firstName ?? '未提供'}>姓名</List.Item>
          <List.Item extra={<Tag color="primary">已登录</Tag>}>状态</List.Item>
        </List>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>偏好设置</div>
        </div>
        <List className={styles.list}>
          <List.Item
            extra={
              <Switch
                checked={theme === 'dark'}
                onChange={(checked) => setTheme(checked ? 'dark' : 'light')}
              />
            }
          >
            深色模式
          </List.Item>
          <List.Item extra="中">默认风险偏好</List.Item>
          <List.Item extra="10,000 USDC">默认投资金额</List.Item>
        </List>
      </div>

      <div className={styles.section}>
        <div className={styles.stack}>
          <Button block color="primary">
            导出记录
          </Button>
          <Button block color="danger" onClick={logout}>
            退出登录
          </Button>
        </div>
      </div>
    </div>
  )
}

export default Settings
