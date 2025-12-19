<template>
  <el-dialog
    v-model="visible"
    title="导入微信账单"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="wechat-import">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" align-center>
        <el-step title="选择文件" description="上传微信账单CSV文件" />
        <el-step title="预览数据" description="确认导入数据" />
        <el-step title="导入设置" description="设置导入参数" />
        <el-step title="导入完成" description="查看导入结果" />
      </el-steps>

      <!-- 步骤1: 选择文件 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="upload-section">
          <el-upload
            ref="uploadRef"
            class="upload-dragger"
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept=".csv"
            :before-upload="beforeUpload"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将微信账单CSV文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传CSV文件，且文件大小不超过10MB
              </div>
            </template>
          </el-upload>

          <!-- 文件信息 -->
          <div v-if="selectedFile" class="file-info">
            <div class="file-item">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
              <el-button
                type="danger"
                link
                size="small"
                @click="removeFile"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 帮助信息 -->
        <div class="help-section">
          <h4>📖 微信账单导出步骤：</h4>
          <ol>
            <li>打开微信，进入「支付」</li>
            <li>点击右上角「···」</li>
            <li>选择「账单」</li>
            <li>点击右上角「常见问题」</li>
            <li>选择「下载账单」</li>
            <li>选择时间范围，选择「CSV」格式</li>
            <li>填写邮箱，等待账单发送到邮箱</li>
            <li>下载CSV文件到本地</li>
          </ol>
        </div>
      </div>

      <!-- 步骤2: 预览数据 -->
      <div v-if="currentStep === 1" class="step-content">
        <div v-if="previewLoading" class="loading-content">
          <el-skeleton :rows="6" animated />
          <p class="loading-text">正在解析账单文件...</p>
        </div>

        <div v-else-if="previewData" class="preview-content">
          <!-- 数据摘要 -->
          <div class="data-summary">
            <h4>📊 数据摘要</h4>
            <div class="summary-grid">
              <div class="summary-item">
                <div class="summary-label">总记录数</div>
                <div class="summary-value">{{ previewData.preview.total_records }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">潜在重复</div>
                <div class="summary-value">{{ previewData.preview.potential_duplicates }}</div>
              </div>
              <div class="summary-item" v-if="summaryData.income_count">
                <div class="summary-label">收入笔数</div>
                <div class="summary-value">{{ summaryData.income_count }}</div>
              </div>
              <div class="summary-item" v-if="summaryData.expense_count">
                <div class="summary-label">支出笔数</div>
                <div class="summary-value">{{ summaryData.expense_count }}</div>
              </div>
            </div>
            <div v-if="summaryData.start_date && summaryData.end_date" class="date-range">
              <strong>时间范围：</strong>{{ summaryData.start_date }} 至 {{ summaryData.end_date }}
            </div>
          </div>

          <!-- 预览表格 -->
          <div class="preview-table">
            <h4>📋 数据预览（前10条）</h4>
            <el-table
              :data="previewData.preview.preview_data"
              size="small"
              max-height="300"
              empty-text="无数据"
            >
              <el-table-column prop="transaction_time" label="交易时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.transaction_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="transaction_type" label="交易类型" width="100" />
              <el-table-column prop="counterparty" label="交易对方" width="120" />
              <el-table-column prop="description" label="商品说明" min-width="150" />
              <el-table-column prop="amount" label="金额" width="100" align="right">
                <template #default="{ row }">
                  <span :class="getAmountClass(row.amount)">
                    ¥{{ Math.abs(row.amount).toFixed(2) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 重复交易提示 -->
          <div v-if="previewData.preview.potential_duplicates > 0" class="warning-section">
            <el-alert
              title="检测到重复交易"
              :description="`发现 ${previewData.preview.potential_duplicates} 条潜在重复交易，建议在导入设置中选择'跳过重复记录'`"
              type="warning"
              show-icon
              :closable="false"
            />
          </div>
        </div>

        <div v-else-if="previewError" class="error-content">
          <el-result
            icon="error"
            title="文件解析失败"
            :sub-title="previewError"
          >
            <template #extra>
              <el-button type="primary" @click="currentStep = 0">
                重新选择文件
              </el-button>
            </template>
          </el-result>
        </div>
      </div>

      <!-- 步骤3: 导入设置 -->
      <div v-if="currentStep === 2" class="step-content">
        <el-form :model="importSettings" label-width="140px" class="settings-form">
          <el-form-item label="跳过重复记录">
            <el-switch
              v-model="importSettings.skip_duplicates"
              active-text="跳过"
              inactive-text="导入"
            />
            <div class="form-tip">
              开启后将跳过与现有交易重复的记录，建议开启
            </div>
          </el-form-item>

          <el-form-item label="智能分类">
            <el-switch
              v-model="importSettings.auto_categorize"
              active-text="开启"
              inactive-text="关闭"
            />
            <div class="form-tip">
              开启后将根据商户名称自动匹配分类，提升记账效率
            </div>
          </el-form-item>

          <el-form-item label="默认账户">
            <el-select
              v-model="importSettings.default_account_id"
              placeholder="选择默认账户"
              style="width: 300px"
              clearable
            >
              <el-option
                v-for="account in accounts"
                :key="account.id"
                :label="`${account.name} (余额: ¥${account.balance})`"
                :value="account.id"
              >
                <div class="account-option">
                  <span class="account-icon">{{ account.icon || '💳' }}</span>
                  <span class="account-name">{{ account.name }}</span>
                  <span class="account-balance">¥{{ account.balance }}</span>
                </div>
              </el-option>
            </el-select>
            <div class="form-tip">
              无法识别支付方式时将使用此账户，建议选择常用的支付账户
            </div>
          </el-form-item>

          <el-form-item label="预计导入记录">
            <div class="import-summary">
              <div class="summary-item">
                <span class="label">总记录数：</span>
                <span class="value">{{ previewData?.preview.total_records || 0 }}</span>
              </div>
              <div class="summary-item" v-if="importSettings.skip_duplicates && previewData?.preview.potential_duplicates">
                <span class="label">预计跳过：</span>
                <span class="value">{{ previewData.preview.potential_duplicates }}</span>
              </div>
              <div class="summary-item">
                <span class="label">预计导入：</span>
                <span class="value highlight">
                  {{ getExpectedImportCount() }}
                </span>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤4: 导入完成 -->
      <div v-if="currentStep === 3" class="step-content">
        <div v-if="importing" class="importing-content">
          <div class="import-animation">
            <el-icon class="loading-icon"><Loading /></el-icon>
          </div>
          <h3>正在导入账单...</h3>
          <p>{{ importProgress.message }}</p>
          <el-progress
            :percentage="importProgress.percentage"
            :status="importProgress.status"
          />
        </div>

        <div v-else-if="importResult" class="result-content">
          <el-result
            :icon="importResult.status === 'success' ? 'success' : 'warning'"
            :title="importResult.status === 'success' ? '导入成功' : '部分成功'"
          >
            <template #sub-title>
              <div class="result-summary">
                <div class="result-item">
                  <span class="label">总记录数：</span>
                  <span class="value">{{ importResult.total_records }}</span>
                </div>
                <div class="result-item success">
                  <span class="label">成功导入：</span>
                  <span class="value">{{ importResult.success_count }}</span>
                </div>
                <div class="result-item error" v-if="importResult.error_count > 0">
                  <span class="label">导入失败：</span>
                  <span class="value">{{ importResult.error_count }}</span>
                </div>
              </div>
            </template>

            <template #extra>
              <el-button @click="handleClose">完成</el-button>
              <el-button
                v-if="importResult.error_count > 0"
                type="primary"
                @click="downloadErrorLog"
              >
                下载错误日志
              </el-button>
            </template>
          </el-result>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          v-if="currentStep > 0 && currentStep < 3"
          @click="prevStep"
        >
          上一步
        </el-button>
        <el-button
          v-if="currentStep < 2"
          type="primary"
          @click="nextStep"
          :disabled="!canNextStep"
        >
          下一步
        </el-button>
        <el-button
          v-if="currentStep === 2"
          type="primary"
          @click="startImport"
          :loading="importing"
        >
          开始导入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled, Document, Loading
} from '@element-plus/icons-vue'
import { importAPI, accountApi } from '@/api'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

// 组件状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const currentStep = ref(0)
const uploadRef = ref()

// 文件相关
const selectedFile = ref<File | null>(null)
const fileContent = ref('')

// 预览相关
const previewLoading = ref(false)
const previewData = ref<any>(null)
const previewError = ref('')
const summaryData = ref<any>({})

// 导入设置
const importSettings = reactive({
  skip_duplicates: true,
  auto_categorize: true,
  default_account_id: null
})

// 导入状态
const importing = ref(false)
const importResult = ref<any>(null)
const importProgress = reactive({
  percentage: 0,
  message: '',
  status: ''
})

// 账户列表
const accounts = ref([])

// 计算属性
const canNextStep = computed(() => {
  if (currentStep.value === 0) {
    return selectedFile.value !== null
  }
  if (currentStep.value === 1) {
    return previewData.value !== null && !previewError.value
  }
  return true
})

// 方法
const loadAccounts = async () => {
  try {
    const response = await accountApi.getAccounts()
    accounts.value = response.accounts || []

    // 设置默认账户
    const defaultAccount = accounts.value.find(acc => acc.is_default)
    if (defaultAccount) {
      importSettings.default_account_id = defaultAccount.id
    }

  } catch (error) {
    console.error('加载账户失败:', error)
  }
}

const beforeUpload = (file: File) => {
  const isCSV = file.name.toLowerCase().endsWith('.csv')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isCSV) {
    ElMessage.error('只能上传CSV格式文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB!')
    return false
  }

  return false // 阻止自动上传
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  readAsText(file.raw)
}

const readAsText = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    fileContent.value = e.target?.result as string
  }
  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }
  reader.readAsText(file, 'UTF-8')
}

const removeFile = () => {
  selectedFile.value = null
  fileContent.value = ''
  previewData.value = null
  previewError.value = ''
  uploadRef.value?.clearFiles()
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getAmountClass = (amount: number) => {
  return amount < 0 ? 'amount-negative' : 'amount-positive'
}

const getExpectedImportCount = () => {
  if (!previewData.value) return 0
  const total = previewData.value.preview.total_records
  const duplicates = importSettings.skip_duplicates ? previewData.value.preview.potential_duplicates : 0
  return Math.max(0, total - duplicates)
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    await previewFile()
  } else if (currentStep.value === 1) {
    // 移动到设置步骤，无需额外操作
  }
  currentStep.value++
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const previewFile = async () => {
  if (!fileContent.value) return

  previewLoading.value = true
  previewError.value = ''

  try {
    const response = await importAPI.previewWechatBill({
      file: new File([fileContent.value], selectedFile.value!.name, { type: 'text/csv' })
    })

    if (response.valid) {
      previewData.value = response
      summaryData.value = response.summary || {}
    } else {
      previewError.value = response.error || '文件格式验证失败'
    }

  } catch (error: any) {
    console.error('预览失败:', error)
    previewError.value = error.response?.data?.message || '预览失败'
  } finally {
    previewLoading.value = false
  }
}

const startImport = async () => {
  if (!fileContent.value || !selectedFile.value) return

  importing.value = true
  importProgress.percentage = 0
  importProgress.message = '正在准备导入数据...'
  importProgress.status = ''

  try {
    importProgress.percentage = 30
    importProgress.message = '正在解析账单数据...'

    // 模拟导入进度
    const progressInterval = setInterval(() => {
      if (importProgress.percentage < 90) {
        importProgress.percentage += 10
        importProgress.message = '正在导入交易记录...'
      }
    }, 500)

    const response = await importAPI.importWechatBill({
      file: new File([fileContent.value], selectedFile.value.name, { type: 'text/csv' }),
      skip_duplicates: importSettings.skip_duplicates,
      auto_categorize: importSettings.auto_categorize,
      default_account_id: importSettings.default_account_id
    })

    clearInterval(progressInterval)

    importProgress.percentage = 100
    importProgress.message = '导入完成！'

    // 处理导入结果
    importResult.value = {
      status: response.failed_records === 0 ? 'success' : 'partial',
      total_records: response.total_records,
      success_count: response.success_records,
      error_count: response.failed_records,
      import_log_id: response.import_log_id
    }

    currentStep.value = 3

    if (response.failed_records === 0) {
      ElMessage.success('账单导入成功！')
    } else {
      ElMessage.warning(`账单部分导入成功，${response.failed_records} 条记录导入失败`)
    }

    emit('success')

  } catch (error: any) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.message || '导入失败')
    importProgress.status = 'exception'
  } finally {
    importing.value = false
  }
}

const downloadErrorLog = async () => {
  if (!importResult.value?.import_log_id) return

  try {
    // 这里需要实现下载错误日志的逻辑
    ElMessage.info('错误日志下载功能开发中...')
  } catch (error) {
    console.error('下载错误日志失败:', error)
    ElMessage.error('下载失败')
  }
}

const handleClose = () => {
  if (importing.value) {
    ElMessage.warning('正在导入中，请稍候...')
    return
  }

  // 重置状态
  currentStep.value = 0
  selectedFile.value = null
  fileContent.value = ''
  previewData.value = null
  previewError.value = ''
  summaryData.value = {}
  importResult.value = null
  importProgress.percentage = 0
  importProgress.message = ''
  importProgress.status = ''

  visible.value = false
}

// 监听弹窗显示状态
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadAccounts()
  }
})
</script>

<style scoped>
.wechat-import {
  padding: 20px 0;
}

.step-content {
  margin-top: 30px;
  min-height: 300px;
}

/* 步骤1: 文件上传 */
.upload-section {
  margin-bottom: 30px;
}

.upload-dragger {
  width: 100%;
}

.file-info {
  margin-top: 20px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
}

.file-name {
  flex: 1;
  font-weight: 500;
}

.file-size {
  color: #909399;
  font-size: 12px;
}

.help-section {
  margin-top: 30px;
  padding: 20px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.help-section h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.help-section ol {
  margin: 0;
  padding-left: 20px;
}

.help-section li {
  margin-bottom: 8px;
  color: #666;
  line-height: 1.5;
}

/* 步骤2: 数据预览 */
.loading-content {
  text-align: center;
}

.loading-text {
  margin-top: 16px;
  color: #666;
}

.preview-content h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.data-summary {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.date-range {
  font-size: 14px;
  color: #666;
}

.preview-table {
  margin-bottom: 20px;
}

.amount-positive {
  color: #67c23a;
}

.amount-negative {
  color: #f56c6c;
}

.warning-section {
  margin-top: 20px;
}

/* 步骤3: 导入设置 */
.settings-form {
  max-width: 600px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.account-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-icon {
  font-size: 16px;
}

.account-name {
  flex: 1;
}

.account-balance {
  color: #909399;
  font-size: 12px;
}

.import-summary {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.import-summary .summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.import-summary .summary-item:last-child {
  margin-bottom: 0;
}

.import-summary .label {
  color: #666;
}

.import-summary .value {
  font-weight: 500;
}

.import-summary .value.highlight {
  color: #409eff;
  font-size: 16px;
}

/* 步骤4: 导入结果 */
.importing-content {
  text-align: center;
  padding: 40px 20px;
}

.import-animation {
  margin-bottom: 20px;
}

.loading-icon {
  font-size: 48px;
  color: #409eff;
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.importing-content h3 {
  margin: 0 0 12px 0;
  color: #333;
}

.importing-content p {
  margin: 0 0 20px 0;
  color: #666;
}

.result-content {
  padding: 20px;
}

.result-summary {
  text-align: left;
  display: inline-block;
}

.result-item {
  display: flex;
  justify-content: space-between;
  min-width: 200px;
  margin-bottom: 8px;
  font-size: 14px;
}

.result-item .label {
  color: #666;
}

.result-item .value {
  font-weight: 500;
}

.result-item.success .value {
  color: #67c23a;
}

.result-item.error .value {
  color: #f56c6c;
}

.dialog-footer {
  text-align: right;
}

@media (max-width: 768px) {
  .step-content {
    margin-top: 20px;
    min-height: 250px;
  }

  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .help-section {
    padding: 16px;
  }

  .settings-form {
    max-width: 100%;
  }
}
</style>