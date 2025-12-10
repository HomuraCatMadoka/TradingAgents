import { useMemo, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button, ErrorBlock, Input, SearchBar, type InputRef } from 'antd-mobile'
import ProtocolCard from '@/components/ProtocolCard'
import LoadingState from '@/components/LoadingState'
import {
  addFavorite,
  deleteFavorite,
  getFavorites,
  type Favorite,
} from '@/services/favorites'
import type { Protocol } from '@/types/protocol'
import styles from './Page.module.css'

const Favorites = () => {
  const [keyword, setKeyword] = useState('')
  const [protocolName, setProtocolName] = useState('')
  const [protocolType, setProtocolType] = useState('')

  const protocolNameRef = useRef<InputRef>(null)
  const protocolTypeRef = useRef<InputRef>(null)

  const getProtocolName = () =>
    (protocolName || protocolNameRef.current?.nativeElement?.value || '').trim()
  const getProtocolType = () =>
    (protocolType || protocolTypeRef.current?.nativeElement?.value || '').trim()

  const {
    data: favorites = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['favorites', 'page'],
    queryFn: () => getFavorites(),
  })

  const addMutation = useMutation({
    mutationFn: (payload: { protocolName: string; protocolType?: string }) =>
      addFavorite(payload),
    onSuccess: () => {
      setProtocolName('')
      setProtocolType('')
      const nameInput = protocolNameRef.current?.nativeElement
      const typeInput = protocolTypeRef.current?.nativeElement
      if (nameInput) nameInput.value = ''
      if (typeInput) typeInput.value = ''
      refetch()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteFavorite(id),
    onSuccess: () => refetch(),
  })

  const filtered = useMemo(
    () =>
      favorites.filter((item) =>
        item.protocolName.toLowerCase().includes(keyword.toLowerCase()),
      ),
    [favorites, keyword],
  )

  const toProtocol = (favorite: Favorite): Protocol => ({
    id: String(favorite.id),
    name: favorite.protocolName,
    slug: favorite.protocolName,
    chain: favorite.protocolType ?? undefined,
    isFavorite: true,
  })

  if (isLoading) return <LoadingState message="加载收藏列表..." />
  if (isError)
    return (
      <div className="space-y-2">
        <ErrorBlock status="default" title="加载失败" description="无法获取收藏列表" />
        <Button size="small" onClick={() => refetch()}>
          重试
        </Button>
      </div>
    )

  return (
    <div className={`${styles.page} space-y-3`}>
      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>添加收藏</div>
        </div>
        <Input
          placeholder="协议名称（必填）"
          value={protocolName}
          onChange={setProtocolName}
          ref={protocolNameRef}
        />
        <Input
          placeholder="协议链/类型（可选）"
          value={protocolType}
          onChange={setProtocolType}
          ref={protocolTypeRef}
        />
        <Button
          color="primary"
          loading={addMutation.isPending}
          onClick={() => {
            const name = getProtocolName()
            if (!name) return
            addMutation.mutate({
              protocolName: name,
              protocolType: getProtocolType(),
            })
          }}
        >
          添加收藏
        </Button>
      </div>

      <div className={`${styles.section} flex flex-col gap-3`}>
        <SearchBar
          placeholder="搜索收藏协议"
          value={keyword}
          onChange={setKeyword}
          showCancelButton
        />
        {filtered.length === 0 ? (
          <ErrorBlock status="empty" title="暂无收藏" description="添加后会显示在这里" />
        ) : (
          filtered.map((item) => (
            <ProtocolCard
              key={item.id}
              protocol={toProtocol(item)}
              subtitle={item.protocolType ?? undefined}
              actions={
                <Button
                  size="mini"
                  color="warning"
                  loading={deleteMutation.isPending}
                  onClick={() => deleteMutation.mutate(item.id)}
                >
                  删除
                </Button>
              }
            />
          ))
        )}
      </div>
    </div>
  )
}

export default Favorites
