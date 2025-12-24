import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  // 认证相关路由（无布局）
  {
    path: '/auth',
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue'),
        meta: { requiresGuest: true, title: '登录' }
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/Register.vue'),
        meta: { requiresGuest: true, title: '注册' }
      },
      {
        path: 'forgot-password',
        name: 'ForgotPassword',
        component: () => import('@/views/auth/ForgotPassword.vue'),
        meta: { requiresGuest: true, title: '忘记密码' }
      }
    ]
  },
  // 主应用路由（带布局）
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/home/Dashboard.vue'),
        meta: { requiresAuth: true, title: '仪表盘' }
      },
      {
        path: 'transactions',
        name: 'Transactions',
        component: () => import('@/views/transaction/TransactionList.vue'),
        meta: { requiresAuth: true, title: '交易记录' }
      },
      {
        path: 'transactions/add',
        name: 'AddTransaction',
        component: () => import('@/views/transaction/AddTransaction.vue'),
        meta: { requiresAuth: true, title: '添加交易' }
      },
      {
        path: 'transactions/:id/edit',
        name: 'EditTransaction',
        component: () => import('@/views/transaction/AddTransaction.vue'),
        meta: { requiresAuth: true, title: '编辑交易' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/statistics/Overview.vue'),
        meta: { requiresAuth: true, title: '统计分析' }
      },
      {
        path: 'wechat/import',
        name: 'WechatImport',
        component: () => import('@/views/import/WechatImport.vue'),
        meta: { requiresAuth: true, title: '微信账单导入' }
      },
      {
        path: 'budgets',
        name: 'Budgets',
        component: () => import('@/views/budget/BudgetList.vue'),
        meta: { requiresAuth: true, title: '预算管理' }
      },
      {
        path: 'budget',
        redirect: '/budgets'
      },
      {
        path: 'reminders',
        name: 'Reminders',
        component: () => import('@/views/reminder/ReminderManagement.vue'),
        meta: { requiresAuth: true, title: '提醒管理' }
      },
      {
        path: 'reminder',
        redirect: '/reminders'
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/account/AccountList.vue'),
        meta: { requiresAuth: true, title: '账户管理' }
      },
      {
        path: 'account',
        redirect: '/accounts'
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { requiresAuth: true, title: '系统设置' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/settings/Profile.vue'),
        meta: { requiresAuth: true, title: '个人资料' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  const title = to.meta?.title as string
  if (title) {
    document.title = `${title} - 个人记账系统`
  } else {
    document.title = '个人记账系统'
  }

  try {
    // 检查是否需要认证
    const requiresAuth = to.matched.some(record => record.meta?.requiresAuth)
    const requiresGuest = to.matched.some(record => record.meta?.requiresGuest)

    // 如果需要认证，检查登录状态
    if (requiresAuth) {
      const hasToken = !!userStore.token
      
      if (!hasToken) {
        // 没有token，跳转到登录页
        ElMessage.warning('请先登录')
        next({
          path: '/auth/login',
          query: { redirect: to.fullPath }
        })
        return
      }
      
      // 有token但没有用户信息，尝试获取
      if (!userStore.user) {
        try {
          await userStore.fetchUserInfo()
        } catch (error) {
          console.error('获取用户信息失败:', error)
          ElMessage.error('登录状态已过期，请重新登录')
          next({
            path: '/auth/login',
            query: { redirect: to.fullPath }
          })
          return
        }
      }
    }

    // 如果需要游客状态但已登录
    if (requiresGuest && userStore.isLoggedIn) {
      next('/dashboard')
      return
    }

    // 通过所有检查，允许访问
    next()
  } catch (error) {
    console.error('路由守卫错误:', error)
    // 出错时，如果是需要认证的页面，跳转到登录页
    if (to.matched.some(record => record.meta?.requiresAuth)) {
      next('/auth/login')
    } else {
      next()
    }
  }
})

// 路由后置守卫
router.afterEach((to, from) => {
  // 可以在这里添加页面访问统计、埋点等逻辑
  console.log(`路由变化: ${from.path} -> ${to.path}`)
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('页面加载失败，请稍后重试')
})

export default router