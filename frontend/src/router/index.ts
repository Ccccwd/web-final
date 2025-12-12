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
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/home/Dashboard.vue'),
    meta: { requiresAuth: true, title: '仪表盘' }
  },
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
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import('@/views/transaction/TransactionList.vue'),
    meta: { requiresAuth: true, title: '交易记录' }
  },
  {
    path: '/transactions/add',
    name: 'AddTransaction',
    component: () => import('@/views/transaction/AddTransaction.vue'),
    meta: { requiresAuth: true, title: '添加交易' }
  },
  {
    path: '/transactions/:id/edit',
    name: 'EditTransaction',
    component: () => import('@/views/transaction/AddTransaction.vue'),
    meta: { requiresAuth: true, title: '编辑交易' }
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: () => import('@/views/statistics/Overview.vue'),
    meta: { requiresAuth: true, title: '统计分析' }
  },
  {
    path: '/budgets',
    name: 'Budgets',
    component: () => import('@/views/budget/BudgetList.vue'),
    meta: { requiresAuth: true, title: '预算管理' }
  },
  {
    path: '/accounts',
    name: 'Accounts',
    component: () => import('@/views/account/AccountList.vue'),
    meta: { requiresAuth: true, title: '账户管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/settings/Settings.vue'),
    meta: { requiresAuth: true, title: '系统设置' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/settings/Profile.vue'),
    meta: { requiresAuth: true, title: '个人资料' }
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

  // 显示加载状态
  const loading = ElMessage.loading({
    message: '加载中...',
    duration: 0,
    customClass: 'route-loading'
  })

  try {
    // 检查是否需要认证
    const requiresAuth = to.matched.some(record => record.meta?.requiresAuth)
    const requiresGuest = to.matched.some(record => record.meta?.requiresGuest)

    // 如果用户未初始化，先初始化
    if (!userStore.isLoggedIn && !userStore.isLoading) {
      await userStore.initializeAuth()
    }

    // 检查认证状态
    if (requiresAuth && !userStore.isLoggedIn) {
      // 需要认证但未登录，跳转到登录页
      ElMessage.warning('请先登录')
      next({
        path: '/auth/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    if (requiresGuest && userStore.isLoggedIn) {
      // 需要游客状态但已登录，跳转到首页
      ElMessage.info('您已经登录')
      next('/dashboard')
      return
    }

    // 通过所有检查，允许访问
    next()
  } catch (error) {
    console.error('路由守卫错误:', error)

    // 发生错误时，根据情况处理
    if (to.matched.some(record => record.meta?.requiresAuth)) {
      ElMessage.error('验证登录状态失败，请重新登录')
      next({
        path: '/auth/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  } finally {
    // 关闭加载状态
    loading.close()
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