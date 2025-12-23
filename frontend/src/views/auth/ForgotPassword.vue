<template>
  <div class="forgot-password-container">
    <el-card class="forgot-password-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>个人记账系统</h2>
          <p>重置密码</p>
        </div>
      </template>

      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" align-center class="steps">
        <el-step title="输入邮箱" description="输入注册邮箱" />
        <el-step title="重置密码" description="设置新密码" />
        <el-step title="完成" description="重置成功" />
      </el-steps>

      <!-- 步骤1: 输入邮箱 -->
      <div v-if="currentStep === 0" class="step-content">
        <el-form
          ref="emailFormRef"
          :model="emailForm"
          :rules="emailRules"
          label-width="0"
          size="large"
          @submit.prevent="handleSendResetEmail"
        >
          <el-form-item prop="email">
            <el-input
              v-model="emailForm.email"
              type="email"
              placeholder="请输入注册邮箱地址"
              prefix-icon="Message"
              clearable
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              class="submit-button"
              :loading="loading"
              @click="handleSendResetEmail"
              size="large"
            >
              {{ loading ? '发送中...' : '发送重置链接' }}
            </el-button>
          </el-form-item>

          <el-form-item>
            <el-button
              class="back-button"
              @click="$router.push('/auth/login')"
              size="large"
            >
              返回登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤2: 重置密码 -->
      <div v-if="currentStep === 1" class="step-content">
        <el-form
          ref="resetFormRef"
          :model="resetForm"
          :rules="resetRules"
          label-width="0"
          size="large"
          @submit.prevent="handleResetPassword"
        >
          <el-alert
            title="重置链接已发送到您的邮箱"
            type="success"
            description="请检查您的邮箱（包括垃圾邮件），然后输入收到的重置令牌"
            :closable="false"
            show-icon
            class="reset-alert"
          />

          <el-form-item prop="token" style="margin-top: 20px;">
            <el-input
              v-model="resetForm.token"
              placeholder="请输入重置令牌"
              prefix-icon="Key"
              clearable
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item prop="new_password">
            <el-input
              v-model="resetForm.new_password"
              type="password"
              placeholder="请输入新密码"
              prefix-icon="Lock"
              show-password
              clearable
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item prop="confirm_password">
            <el-input
              v-model="confirmPassword"
              type="password"
              placeholder="请确认新密码"
              prefix-icon="Lock"
              show-password
              clearable
              :disabled="loading"
              @keyup.enter="handleResetPassword"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              class="submit-button"
              :loading="loading"
              @click="handleResetPassword"
              size="large"
            >
              {{ loading ? '重置中...' : '重置密码' }}
            </el-button>
          </el-form-item>

          <el-form-item>
            <el-button
              class="back-button"
              @click="currentStep = 0"
              size="large"
            >
              上一步
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤3: 完成 -->
      <div v-if="currentStep === 2" class="step-content">
        <el-result
          icon="success"
          title="密码重置成功"
          sub-title="您的密码已成功重置，请使用新密码登录"
        >
          <template #extra>
            <el-button
              type="primary"
              @click="$router.push('/auth/login')"
              size="large"
            >
              立即登录
            </el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import { Message, Lock, Key } from '@element-plus/icons-vue'
import { http } from '@/utils'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)

// 表单引用
const emailFormRef = ref<InstanceType<typeof ElForm>>()
const resetFormRef = ref<InstanceType<typeof ElForm>>()

// 邮箱表单数据
const emailForm = reactive({
  email: ''
})

// 重置密码表单数据
const resetForm = reactive({
  token: '',
  new_password: ''
})

// 确认密码
const confirmPassword = ref('')

// 加载状态
const loading = ref(false)

// 密码验证器
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== resetForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 邮箱表单验证规则
const emailRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email' as const, message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 重置密码表单验证规则
const resetRules = {
  token: [
    { required: true, message: '请输入重置令牌', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 发送重置邮箱
const handleSendResetEmail = async () => {
  if (!emailFormRef.value) return

  try {
    const valid = await emailFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const response = await http.post('/auth/password-reset-request', emailForm)

    if (response.success) {
      ElMessage.success('重置链接已发送到您的邮箱')
      currentStep.value = 1
    }
  } catch (error) {
    console.error('Send reset email error:', error)
  } finally {
    loading.value = false
  }
}

// 重置密码
const handleResetPassword = async () => {
  if (!resetFormRef.value) return

  try {
    const valid = await resetFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const response = await http.post('/auth/password-reset', {
      token: resetForm.token,
      new_password: resetForm.new_password
    })

    if (response.success) {
      ElMessage.success('密码重置成功')
      currentStep.value = 2
    }
  } catch (error) {
    console.error('Reset password error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.forgot-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.forgot-password-card {
  width: 100%;
  max-width: 500px;
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  text-align: center;
  margin-bottom: 10px;
}

.card-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.steps {
  margin: 30px 0 40px;
}

.step-content {
  margin-top: 20px;
}

.reset-alert {
  margin-bottom: 20px;
}

.submit-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
}

.back-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
  color: #409eff;
  border: 1px solid #409eff;
  background: transparent;
}

.back-button:hover {
  background: #ecf5ff;
  border-color: #66b1ff;
  color: #66b1ff;
}

:deep(.el-card__header) {
  padding: 30px 30px 20px;
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-card__body) {
  padding: 30px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-input__wrapper) {
  height: 44px;
  border-radius: 6px;
}

:deep(.el-steps) {
  margin-bottom: 30px;
}

:deep(.el-result) {
  padding: 40px 0;
}
</style>