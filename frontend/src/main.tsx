import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// 初始化认证状态（从 localStorage 恢复）
import { useAuthStore } from './stores/auth-store'
useAuthStore.getState().loadFromStorage()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
