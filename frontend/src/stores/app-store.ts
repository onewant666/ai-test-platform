// 全局应用状态
import { create } from 'zustand'

type ThemeMode = 'light' | 'dark'
type SidebarMode = 'inline' | 'vertical'

interface AppState {
  theme: ThemeMode
  sidebarCollapsed: boolean
  sidebarMode: SidebarMode
  breadcrumbs: { title: string; path?: string }[]

  toggleTheme: () => void
  toggleSidebar: () => void
  setBreadcrumbs: (items: { title: string; path?: string }[]) => void
}

export const useAppStore = create<AppState>((set) => ({
  theme: (localStorage.getItem('app_theme') as ThemeMode) || 'light',
  sidebarCollapsed: false,
  sidebarMode: 'inline',
  breadcrumbs: [],

  toggleTheme: () =>
    set((state) => {
      const next = state.theme === 'light' ? 'dark' : 'light'
      localStorage.setItem('app_theme', next)
      return { theme: next }
    }),

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setBreadcrumbs: (items) => set({ breadcrumbs: items }),
}))
