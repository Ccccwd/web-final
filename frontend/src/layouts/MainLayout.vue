<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <el-header class="app-header" height="60px">
      <div class="header-left">
        <h1 class="app-title">
          <el-icon><Wallet /></el-icon>
          个人记账系统
        </h1>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="36" :src="userStore.avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <span class="username">{{ userStore.username }}</span>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人资料
              </el-dropdown-item>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                系统设置
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container class="app-container">
      <!-- 侧边栏 -->
      <el-aside class="app-aside" :width="isCollapse ? '64px' : '200px'">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="true"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <el-menu-item index="/transactions">
            <el-icon><Tickets /></el-icon>
            <template #title>交易记录</template>
          </el-menu-item>

          <el-menu-item index="/transactions/add">
            <el-icon><Plus /></el-icon>
            <template #title>记一笔</template>
          </el-menu-item>

          <el-menu-item index="/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>统计分析</template>
          </el-menu-item>

          <el-menu-item index="/budgets">
            <el-icon><Money /></el-icon>
            <template #title>预算管理</template>
          </el-menu-item>

          <el-menu-item index="/accounts">
            <el-icon><CreditCard /></el-icon>
            <template #title>账户管理</template>
          </el-menu-item>

          <el-menu-item index="/reminders">
            <el-icon><BellFilled /></el-icon>
            <template #title>提醒管理</template>
          </el-menu-item>

          <el-menu-item index="/wechat/import">
            <el-icon><Upload /></el-icon>
            <template #title>导入账单</template>
          </el-menu-item>
        </el-menu>

        <div class="collapse-toggle" @click="isCollapse = !isCollapse">
          <el-icon v-if="isCollapse"><Expand /></el-icon>
          <el-icon v-else><Fold /></el-icon>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="app-main">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Wallet, User, ArrowDown, Setting, SwitchButton,
  Odometer, Tickets, Plus, DataAnalysis, Money,
  CreditCard, BellFilled, Upload, Expand, Fold
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

const activeMenu = computed(() => {
  const path = route.path
  // 处理编辑页面等动态路由
  if (path.includes('/transactions') && path.includes('/edit')) {
    return '/transactions'
  }
  return path
})

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '退出确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await userStore.logout()
        ElMessage.success('已退出登录')
        router.push('/auth/login')
      } catch (error) {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.app-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.app-title .el-icon {
  font-size: 24px;
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #606266;
}

.dropdown-icon {
  font-size: 12px;
  color: #909399;
}

.app-container {
  flex: 1;
  overflow: hidden;
}

.app-aside {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  position: relative;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
}

.collapse-toggle {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-top: 1px solid #e4e7ed;
  color: #909399;
  transition: all 0.3s;
}

.collapse-toggle:hover {
  background: #f5f7fa;
  color: #409eff;
}

.app-main {
  background: #f5f7fa;
  overflow-y: auto;
  padding: 0;
}

/* 页面切换动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
