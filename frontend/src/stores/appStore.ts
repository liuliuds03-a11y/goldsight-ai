import { create } from 'zustand'

/** 应用全局状态 */
interface AppState {
  /** 侧边栏是否折叠 */
  sidebarCollapsed: boolean
  /** 切换侧边栏 */
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}))
