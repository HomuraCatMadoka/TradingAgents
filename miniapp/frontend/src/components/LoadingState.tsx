import { DotLoading } from 'antd-mobile'
import styles from './LoadingState.module.css'

type Props = {
  message?: string
}

const LoadingState = ({ message = '加载中...' }: Props) => {
  return (
    <div className={styles.wrapper}>
      <DotLoading color="primary" />
      <div className={styles.message}>{message}</div>
    </div>
  )
}

export default LoadingState
