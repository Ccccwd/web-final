<template>
  <div class="not-found-container">
    <el-result
      icon="warning"
      title="404"
      sub-title="抱歉，您访问的页面不存在"
    >
      <template #extra>
        <el-button type="primary" @click="goHome" size="large">
          返回首页
        </el-button>
        <el-button @click="goBack" size="large">
          返回上页
        </el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

:deep(.el-result) {
  padding: 40px 0;
}

:deep(.el-result__icon) {
  font-size: 80px;
}

:deep(.el-result__title) {
  font-size: 48px;
  margin: 20px 0;
}

:deep(.el-result__subtitle) {
  font-size: 16px;
  color: #666;
}

:deep(.el-result__extra) {
  margin-top: 30px;
}

:deep(.el-result__extra .el-button) {
  margin: 0 10px;
}
</style>