<template>
  <div class="register">
    <h2>注册</h2>
    <form>
      <div class="form-group">
        <label>用户名:</label>
        <input type="text" v-model="username" />
      </div>
      <div class="form-group">
        <label>邮箱:</label>
        <input type="email" v-model="email" />
      </div>
      <div class="form-group">
        <label>密码:</label>
        <input type="password" v-model="password" />
      </div>
      <button type="submit">注册</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const username = ref('')
const email = ref('')
const password = ref('')
</script>

<style scoped>
.register {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>