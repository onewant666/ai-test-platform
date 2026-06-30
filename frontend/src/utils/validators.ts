// 表单校验规则

import type { Rule } from 'antd/es/form'

export const usernameRules: Rule[] = [
  { required: true, message: '请输入用户名' },
  { min: 3, max: 32, message: '用户名长度 3-32 个字符' },
]

export const passwordRules: Rule[] = [
  { required: true, message: '请输入密码' },
  { min: 6, max: 64, message: '密码长度 6-64 个字符' },
]

export const emailRules: Rule[] = [
  { type: 'email', message: '请输入有效的邮箱地址' },
]

export const requiredRule = (label: string): Rule => ({
  required: true,
  message: `请输入${label}`,
})

export const urlRule: Rule = {
  type: 'url',
  message: '请输入有效的 URL 地址',
}
