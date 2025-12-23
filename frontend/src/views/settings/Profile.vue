<template>
  <div class="profile-container">
    <el-card class="profile-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h3>个人资料</h3>
          <p>管理您的个人信息</p>
        </div>
      </template>

      <div class="profile-content">
        <!-- 头像部分 -->
        <div class="avatar-section">
          <el-avatar :size="100" :src="userInfo.avatar" class="avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <div class="avatar-actions">
            <el-button type="primary" size="small" @click="handleAvatarUpload">
              更换头像
            </el-button>
          </div>
        </div>

        <!-- 基本信息表单 -->
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-width="120px"
          size="large"
          class="profile-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="profileForm.username"
              placeholder="请输入用户名"
              :disabled="!editMode"
              clearable
            />
          </el-form-item>

          <el-form-item label="邮箱地址" prop="email">
            <el-input
              v-model="profileForm.email"
              type="email"
              placeholder="请输入邮箱地址"
              :disabled="!editMode"
              clearable
            />
          </el-form-item>

          <el-form-item label="手机号码" prop="phone">
            <el-input
              v-model="profileForm.phone"
              placeholder="请输入手机号码"
              :disabled="!editMode"
              clearable
            />
          </el-form-item>

          <el-form-item label="注册时间">
            <el-input
              :model-value="formatDate(userInfo.created_at)"
              disabled
            />
          </el-form-item>

          <el-form-item>
            <div class="form-actions">
              <template v-if="!editMode">
                <el-button type="primary" @click="enterEditMode">
                  编辑资料
                </el-button>
              </template>
              <template v-else>
                <el-button type="primary" :loading="loading" @click="handleSave">
                  保存修改
                </el-button>
                <el-button @click="cancelEdit">
                  取消
                </el-button>
              </template>
            </div>
          </el-form-item>
        </el-form>

        <!-- 修改密码部分 -->
        <el-divider content-position="left">
          <span class="divider-text">修改密码</span>
        </el-divider>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="120px"
          size="large"
          class="password-form"
        >
          <el-form-item label="当前密码" prop="current_password">
            <el-input
              v-model="passwordForm.current_password"
              type="password"
              placeholder="请输入当前密码"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="请输入新密码"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input
              v-model="confirmPassword"
              type="password"
              placeholder="请确认新密码"
              show-password
              clearable
              @keyup.enter="handlePasswordChange"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="warning"
              :loading="passwordLoading"
              @click="handlePasswordChange"
            >
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import { formatDate } from '@/utils'

const userStore = useUserStore()

// 表单引用
const profileFormRef = ref<InstanceType<typeof ElForm>>()
const passwordFormRef = ref<InstanceType<typeof ElForm>>()

// 编辑模式
const editMode = ref(false)

// 加载状态
const loading = ref(false)
const passwordLoading = ref(false)

// 用户信息
const userInfo = computed(() => userStore.user || {
  username: '',
  email: '',
  phone: '',
  avatar: '',
  created_at: new Date()
})

// 原始表单数据（用于取消编辑）
const originalProfileForm = ref<any>({})

// 个人信息表单
const profileForm = reactive({
  username: '',
  email: '',
  phone: ''
})

// 密码表单
const passwordForm = reactive({
  current_password: '',
  new_password: ''
})

// 确认密码
const confirmPassword = ref('')

// 确认密码验证器
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 个人信息表单验证规则
const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email' as const, message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

// 密码表单验证规则
const passwordRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
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

// 初始化表单数据
const initForm = () => {
  profileForm.username = userInfo.value.username
  profileForm.email = userInfo.value.email
  profileForm.phone = userInfo.value.phone || ''

  // 保存原始数据
  originalProfileForm.value = { ...profileForm }
}

// 进入编辑模式
const enterEditMode = () => {
  editMode.value = true
  originalProfileForm.value = { ...profileForm }
}

// 取消编辑
const cancelEdit = () => {
  editMode.value = false
  Object.assign(profileForm, originalProfileForm.value)
}

// 保存个人信息
const handleSave = async () => {
  if (!profileFormRef.value) return

  try {
    const valid = await profileFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const success = await userStore.updateUserInfo(profileForm)

    if (success) {
      editMode.value = false
      // 刷新用户信息
      await userStore.fetchUserInfo()
    }
  } catch (error) {
    console.error('Save profile error:', error)
  } finally {
    loading.value = false
  }
}

// 修改密码
const handlePasswordChange = async () => {
  if (!passwordFormRef.value) return

  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return

    passwordLoading.value = true

    const success = await userStore.changePassword(
      passwordForm.current_password,
      passwordForm.new_password
    )

    if (success) {
      // 清空密码表单
      passwordForm.current_password = ''
      passwordForm.new_password = ''
      confirmPassword.value = ''

      // 重置表单验证
      passwordFormRef.value.resetFields()
    }
  } catch (error) {
    console.error('Change password error:', error)
  } finally {
    passwordLoading.value = false
  }
}

// 头像上传（暂时只是提示）
const handleAvatarUpload = () => {
  ElMessage.info('头像上传功能暂未开放，敬请期待')
}

// 页面加载时初始化
onMounted(() => {
  initForm()
})
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-card {
  border-radius: 12px;
}

.card-header {
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.profile-content {
  display: grid;
  gap: 30px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.avatar {
  border: 3px solid #e4e7ed;
}

.avatar-actions {
  display: flex;
  gap: 10px;
}

.profile-form {
  max-width: 500px;
  margin: 0 auto;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.divider-text {
  color: #909399;
  font-weight: 500;
}

.password-form {
  max-width: 500px;
  margin: 0 auto;
}

:deep(.el-card__header) {
  padding: 25px 30px 15px;
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-card__body) {
  padding: 30px;
}

:deep(.el-form-item) {
  margin-bottom: 25px;
}

:deep(.el-input__wrapper) {
  height: 44px;
  border-radius: 6px;
}

:deep(.el-divider) {
  margin: 30px 0 25px;
}

:deep(.el-divider__text) {
  background-color: #fff;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 15px;
  }

  :deep(.el-form-item__label) {
    text-align: left;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>