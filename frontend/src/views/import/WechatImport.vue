<template>
  <div class="wechat-import-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>微信账单导入</h2>
          <p class="subtitle">支持导入微信支付账单，自动识别交易记录</p>
        </div>
      </template>
      
      <div class="import-content">
        <el-empty v-if="!showDialog" description="点击下方按钮开始导入微信账单">
          <el-button type="primary" size="large" @click="showDialog = true">
            <el-icon><Upload /></el-icon>
            开始导入
          </el-button>
        </el-empty>
        
        <div v-else class="import-history">
          <h3>导入历史</h3>
          <el-button type="primary" @click="showDialog = true">
            <el-icon><Plus /></el-icon>
            新建导入
          </el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 导入对话框 -->
    <WechatImportComponent 
      v-model="showDialog"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Plus } from '@element-plus/icons-vue'
import WechatImportComponent from '@/components/import/WechatImport.vue'

const showDialog = ref(false)

const handleImportSuccess = () => {
  ElMessage.success('导入成功！')
  showDialog.value = false
}
</script>

<style scoped>
.wechat-import-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 8px 0 0;
  color: #909399;
  font-size: 14px;
}

.import-content {
  padding: 40px 20px;
  min-height: 400px;
}

.import-history {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.import-history h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
</style>
