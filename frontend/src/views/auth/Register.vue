<template>
  <div class="register-container">
    <el-card class="register-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>个人记账系统</h2>
          <p>创建新账户</p>
        </div>
      </template>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="0"
        size="large"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            clearable
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            type="email"
            placeholder="请输入邮箱地址"
            prefix-icon="Message"
            clearable
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item prop="phone">
          <el-input
            v-model="registerForm.phone"
            placeholder="请输入手机号码（可选）"
            prefix-icon="Phone"
            clearable
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            clearable
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="confirmPassword"
            type="password"
            placeholder="请确认密码"
            prefix-icon="Lock"
            show-password
            clearable
            :disabled="loading"
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="agreeToTerms" :disabled="loading">
            我已阅读并同意
            <a href="#" class="terms-link" @click.prevent="showTerms">用户协议</a>
            和
            <a href="#" class="terms-link" @click.prevent="showPrivacy">隐私政策</a>
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="register-button"
            :loading="loading"
            :disabled="!agreeToTerms"
            @click="handleRegister"
            size="large"
          >
            {{ loading ? '注册中...' : '立即注册' }}
          </el-button>
        </el-form-item>

        <el-divider>
          <span class="divider-text">已有账户？</span>
        </el-divider>

        <el-form-item>
          <el-button
            class="login-button"
            @click="$router.push('/auth/login')"
            size="large"
          >
            返回登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { User, Lock, Message, Phone } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import type { UserCreate } from '@/types'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const registerFormRef = ref<InstanceType<typeof ElForm>>()

// 表单数据
const registerForm = reactive<UserCreate>({
  username: '',
  email: '',
  password: '',
  phone: ''
})

// 确认密码
const confirmPassword = ref('')

// 同意条款
const agreeToTerms = ref(false)

// 加载状态
const loading = ref(false)

// 密码验证器
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  if (!agreeToTerms.value) {
    ElMessage.warning('请先同意用户协议和隐私政策')
    return
  }

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const success = await userStore.register(registerForm)

    if (success) {
      ElMessageBox.alert(
        '注册成功！请使用您的账户信息登录。',
        '注册成功',
        {
          confirmButtonText: '前往登录',
          type: 'success'
        }
      ).then(() => {
        router.push('/auth/login')
      })
    }
  } catch (error) {
    console.error('Register error:', error)
  } finally {
    loading.value = false
  }
}

// 显示用户协议
const showTerms = () => {
  ElMessageBox.alert(
    '1. 用户应当提供真实、准确的注册信息\n' +
    '2. 用户有义务保护个人账户和密码的安全\n' +
    '3. 用户应当遵守相关法律法规，不得利用本服务从事违法活动\n' +
    '4. 本服务仅供个人记账使用，不得用于商业用途\n' +
    '5. 我们保留根据业务需要修改服务条款的权利',
    '用户协议',
    {
      confirmButtonText: '我已了解',
      type: 'info'
    }
  )
}

// 显示隐私政策
const showPrivacy = () => {
  ElMessageBox.alert(
    '1. 我们承诺保护您的个人隐私信息\n' +
    '2. 收集的信息仅用于改善服务质量\n' +
    '3. 未经您的同意，不会向第三方分享您的个人信息\n' +
    '4. 我们采用合理的技术手段保护您的数据安全\n' +
    '5. 您有权随时查看、修改或删除您的个人信息',
    '隐私政策',
    {
      confirmButtonText: '我已了解',
      type: 'info'
    }
  )
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 450px;
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

.terms-link {
  color: #409eff;
  text-decoration: none;
}

.terms-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.register-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
  color: #409eff;
  border: 1px solid #409eff;
  background: transparent;
}

.login-button:hover {
  background: #ecf5ff;
  border-color: #66b1ff;
  color: #66b1ff;
}

.divider-text {
  color: #909399;
  font-size: 14px;
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

:deep(.el-divider) {
  margin: 24px 0 20px;
}

:deep(.el-checkbox) {
  font-size: 14px;
  line-height: 1.5;
}
</style>