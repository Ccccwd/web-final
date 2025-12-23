<template>
  <div class="reminder-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>智能提醒</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          添加提醒
        </el-button>
        <el-button @click="checkDailyReminder">
          <el-icon><Bell /></el-icon>
          检查今日提醒
        </el-button>
      </div>
    </div>

    <!-- 提醒统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reminderStats.total_reminders || 0 }}</div>
              <div class="stat-label">总提醒数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reminderStats.enabled_reminders || 0 }}</div>
              <div class="stat-label">启用提醒</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reminderStats.type_stats?.daily || 0 }}</div>
              <div class="stat-label">每日记账</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reminderStats.type_stats?.budget || 0 }}</div>
              <div class="stat-label">预算提醒</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.type" placeholder="提醒类型" clearable @change="loadReminders">
            <el-option label="全部类型" value="" />
            <el-option label="每日记账" value="daily" />
            <el-option label="预算提醒" value="budget" />
            <el-option label="循环提醒" value="recurring" />
            <el-option label="分析报告" value="report" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.is_enabled" placeholder="状态" clearable @change="loadReminders">
            <el-option label="全部状态" value="" />
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="12">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="loadReminders">刷新</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 提醒列表 -->
    <div class="reminder-list">
      <el-table :data="reminders" v-loading="loading" stripe>
        <el-table-column prop="title" label="提醒标题" min-width="180">
          <template #default="{ row }">
            <div class="reminder-title">
              <el-icon class="reminder-icon" :style="{ color: getReminderTypeColor(row.type) }">
                <component :is="getReminderIcon(row.type)" />
              </el-icon>
              <span>{{ row.title || getDefaultTitle(row.type) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getReminderTypeTag(row.type)">
              {{ getReminderTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="提醒时间" width="150">
          <template #default="{ row }">
            <div v-if="row.remind_time">
              <div>{{ formatTime(row.remind_time) }}</div>
              <small v-if="row.remind_day" class="text-gray-500">
                每月{{ row.remind_day }}日
              </small>
            </div>
            <span v-else class="text-gray-400">未设置</span>
          </template>
        </el-table-column>

        <el-table-column label="关联分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.category_name" type="info" size="small">
              {{ row.category_name }}
            </el-tag>
            <span v-else class="text-gray-400">无</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="toggleReminderStatus(row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="last_reminded_at" label="最后提醒" width="150">
          <template #default="{ row }">
            <span v-if="row.last_reminded_at">
              {{ formatDateTime(row.last_reminded_at) }}
            </span>
            <span v-else class="text-gray-400">从未提醒</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editReminder(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteReminder(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 提醒模板 -->
    <div class="reminder-templates">
      <h3>快速创建提醒模板</h3>
      <el-row :gutter="15">
        <el-col :span="6">
          <el-card class="template-card" @click="createFromTemplate('daily')">
            <div class="template-content">
              <el-icon class="template-icon"><Clock /></el-icon>
              <div class="template-title">每日记账提醒</div>
              <div class="template-desc">每天定时提醒记账</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="template-card" @click="createFromTemplate('budget')">
            <div class="template-content">
              <el-icon class="template-icon"><Warning /></el-icon>
              <div class="template-title">预算使用提醒</div>
              <div class="template-desc">预算超支时提醒</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="template-card" @click="createFromTemplate('report')">
            <div class="template-content">
              <el-icon class="template-icon"><DataAnalysis /></el-icon>
              <div class="template-title">月度分析报告</div>
              <div class="template-desc">每月财务分析报告</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="template-card" @click="createFromTemplate('recurring')">
            <div class="template-content">
              <el-icon class="template-icon"><Refresh /></el-icon>
              <div class="template-title">循环提醒</div>
              <div class="template-desc">定期循环提醒事项</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 创建/编辑提醒对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingReminder ? '编辑提醒' : '添加提醒'"
      width="600px"
    >
      <el-form :model="reminderForm" :rules="reminderRules" ref="reminderFormRef" label-width="100px">
        <el-form-item label="提醒类型" prop="type">
          <el-select v-model="reminderForm.type" placeholder="选择提醒类型" style="width: 100%" @change="onTypeChange">
            <el-option label="每日记账" value="daily" />
            <el-option label="预算提醒" value="budget" />
            <el-option label="循环提醒" value="recurring" />
            <el-option label="分析报告" value="report" />
          </el-select>
        </el-form-item>

        <el-form-item label="提醒标题" prop="title">
          <el-input v-model="reminderForm.title" placeholder="请输入提醒标题" />
        </el-form-item>

        <el-form-item label="提醒内容">
          <el-input v-model="reminderForm.content" type="textarea" :rows="3" placeholder="请输入提醒内容" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="提醒时间" prop="remind_time" v-if="needRemindTime">
              <el-time-picker
                v-model="reminderForm.remind_time"
                placeholder="选择提醒时间"
                format="HH:mm"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="提醒日期" prop="remind_day" v-if="reminderForm.type === 'recurring'">
              <el-input-number
                v-model="reminderForm.remind_day"
                :min="1"
                :max="31"
                placeholder="每月第几天"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="关联分类" prop="category_id" v-if="reminderForm.type === 'budget'">
          <el-select v-model="reminderForm.category_id" placeholder="选择分类" style="width: 100%" clearable>
            <el-option
              v-for="category in expenseCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="提醒金额" v-if="reminderForm.type === 'recurring'">
          <el-input-number
            v-model="reminderForm.amount"
            :min="0"
            :precision="2"
            placeholder="固定金额（可选）"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="reminderForm.is_enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="cancelEdit">取消</el-button>
        <el-button type="primary" @click="saveReminder" :loading="saveLoading">
          {{ editingReminder ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Bell, Clock, Warning, DataAnalysis, Refresh } from '@element-plus/icons-vue'
import { reminderApi } from '@/api/reminders'
import * as categoryApi from '@/api/category'
import { formatDateTime, formatTime } from '@/utils/format'

// 类型定义
interface ReminderStats {
  total_reminders: number
  enabled_reminders: number
  disabled_reminders: number
  type_stats: Record<string, number>
}

// 响应式数据
const loading = ref(false)
const reminders = ref([])
const reminderStats = ref<ReminderStats>({
  total_reminders: 0,
  enabled_reminders: 0,
  disabled_reminders: 0,
  type_stats: {}
})
const expenseCategories = ref([])
const showCreateDialog = ref(false)
const editingReminder = ref(null)
const saveLoading = ref(false)

// 筛选条件
const filters = reactive({
  type: '',
  is_enabled: null
})

// 表单数据
const reminderForm = reactive({
  type: '',
  title: '',
  content: '',
  remind_time: null,
  remind_day: null,
  category_id: null,
  amount: null,
  is_enabled: true
})

// 表单验证规则
const reminderRules = {
  type: [{ required: true, message: '请选择提醒类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入提醒标题', trigger: 'blur' }],
  remind_time: [{ required: true, message: '请选择提醒时间', trigger: 'change' }],
  category_id: [{ required: true, message: '请选择关联分类', trigger: 'change' }]
}

// 计算属性
const needRemindTime = computed(() => {
  return ['daily', 'recurring', 'report'].includes(reminderForm.type)
})

// 方法定义
const loadReminders = async () => {
  try {
    loading.value = true
    const params: Record<string, any> = {}
    if (filters.type) params.type = filters.type
    if (filters.is_enabled !== null) params.is_enabled = filters.is_enabled

    const response = await reminderApi.getReminders(params)
    reminders.value = response.data.data.reminders

    // 加载提醒统计
    const statsResponse = await reminderApi.getReminderStatistics()
    reminderStats.value = statsResponse.data.data || reminderStats.value
  } catch (error) {
    ElMessage.error('加载提醒列表失败')
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const response = await categoryApi.getCategories()
    expenseCategories.value = response.data.data.filter((c: any) => c.type === 'expense')
  } catch (error) {
    console.error('加载分类列表失败:', error)
  }
}

const resetFilters = () => {
  filters.type = ''
  filters.is_enabled = null
  loadReminders()
}

const getReminderTypeName = (type) => {
  const typeMap = {
    daily: '每日记账',
    budget: '预算提醒',
    recurring: '循环提醒',
    report: '分析报告'
  }
  return typeMap[type] || type
}

const getReminderTypeTag = (type) => {
  const tagMap = {
    daily: 'primary',
    budget: 'warning',
    recurring: 'success',
    report: 'info'
  }
  return tagMap[type] || ''
}

const getReminderTypeColor = (type) => {
  const colorMap = {
    daily: '#409EFF',
    budget: '#E6A23C',
    recurring: '#67C23A',
    report: '#909399'
  }
  return colorMap[type] || '#909399'
}

const getReminderIcon = (type) => {
  const iconMap = {
    daily: Clock,
    budget: Warning,
    recurring: Refresh,
    report: DataAnalysis
  }
  return iconMap[type] || Bell
}

const getDefaultTitle = (type) => {
  const titleMap = {
    daily: '每日记账提醒',
    budget: '预算使用提醒',
    recurring: '循环提醒',
    report: '分析报告提醒'
  }
  return titleMap[type] || '提醒'
}

const toggleReminderStatus = async (reminder) => {
  try {
    await reminderApi.updateReminder(reminder.id, { is_enabled: reminder.is_enabled })
    ElMessage.success('提醒状态更新成功')
  } catch (error) {
    reminder.is_enabled = !reminder.is_enabled // 回滚状态
    ElMessage.error('更新提醒状态失败')
  }
}

const editReminder = (reminder) => {
  editingReminder.value = reminder
  Object.assign(reminderForm, {
    type: reminder.type,
    title: reminder.title,
    content: reminder.content,
    remind_time: reminder.remind_time,
    remind_day: reminder.remind_day,
    category_id: reminder.category_id,
    amount: reminder.amount,
    is_enabled: reminder.is_enabled
  })
  showCreateDialog.value = true
}

const saveReminder = async () => {
  try {
    saveLoading.value = true
    const formData: any = { ...reminderForm }

    // 处理时间格式
    if (formData.remind_time) {
      formData.remind_time = formatTime(formData.remind_time)
    }

    if (editingReminder.value) {
      await reminderApi.updateReminder(editingReminder.value.id, formData)
      ElMessage.success('提醒更新成功')
    } else {
      await reminderApi.createReminder(formData)
      ElMessage.success('提醒创建成功')
    }
    showCreateDialog.value = false
    loadReminders()
  } catch (error) {
    ElMessage.error('保存提醒失败')
  } finally {
    saveLoading.value = false
  }
}

const cancelEdit = () => {
  showCreateDialog.value = false
  editingReminder.value = null
  Object.assign(reminderForm, {
    type: '',
    title: '',
    content: '',
    remind_time: null,
    remind_day: null,
    category_id: null,
    amount: null,
    is_enabled: true
  })
}

const deleteReminder = async (reminder) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除提醒"${reminder.title || getDefaultTitle(reminder.type)}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await reminderApi.deleteReminder(reminder.id)
    ElMessage.success('提醒删除成功')
    loadReminders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除提醒失败')
    }
  }
}

const checkDailyReminder = async () => {
  try {
    const response = await reminderApi.checkDailyReminder()
    if (response.data.data.reminder_created) {
      ElMessage.success('已为您创建每日记账提醒')
    } else {
      ElMessage.info(response.data.data.message || '暂无需创建提醒')
    }
    loadReminders()
  } catch (error) {
    ElMessage.error('检查每日提醒失败')
  }
}

const createFromTemplate = async (templateType) => {
  try {
    const response = await reminderApi.getTemplate(templateType)
    const template = response.data.data

    Object.assign(reminderForm, {
      type: template.type,
      title: template.title,
      content: template.content,
      remind_time: template.remind_time,
      remind_day: template.remind_day,
      category_id: null,
      amount: null,
      is_enabled: template.is_enabled
    })

    showCreateDialog.value = true
  } catch (error) {
    ElMessage.error('加载模板失败')
  }
}

const onTypeChange = () => {
  // 类型变化时清空相关字段
  reminderForm.remind_day = null
  reminderForm.category_id = null

  // 根据类型设置默认值
  if (reminderForm.type === 'daily') {
    reminderForm.title = reminderForm.title || '每日记账提醒'
    reminderForm.content = reminderForm.content || '记得今天记账哦！保持良好的记账习惯。'
  } else if (reminderForm.type === 'budget') {
    reminderForm.title = reminderForm.title || '预算使用提醒'
    reminderForm.content = reminderForm.content || '您的预算使用率已较高，请注意控制支出。'
  } else if (reminderForm.type === 'report') {
    reminderForm.title = reminderForm.title || '月度分析报告'
    reminderForm.content = reminderForm.content || '您的月度财务报告已生成，请查看详细分析。'
    reminderForm.remind_day = reminderForm.remind_day || 1
  } else if (reminderForm.type === 'recurring') {
    reminderForm.title = reminderForm.title || '循环提醒'
    reminderForm.content = reminderForm.content || '这是一个定期提醒，请注意相关事项。'
  }
}

// 生命周期
onMounted(() => {
  loadReminders()
  loadCategories()
})
</script>

<style scoped>
.reminder-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.reminder-list {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 30px;
}

.reminder-title {
  display: flex;
  align-items: center;
}

.reminder-icon {
  margin-right: 8px;
  font-size: 18px;
}

.reminder-templates {
  margin-top: 30px;
}

.reminder-templates h3 {
  margin-bottom: 15px;
  color: #303133;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409EFF;
}

.template-content {
  text-align: center;
  padding: 20px 10px;
}

.template-icon {
  font-size: 32px;
  color: #409EFF;
  margin-bottom: 10px;
}

.template-title {
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.template-desc {
  font-size: 12px;
  color: #909399;
}

.text-gray-400 {
  color: #909399;
}

.text-gray-500 {
  color: #C0C4CC;
}
</style>