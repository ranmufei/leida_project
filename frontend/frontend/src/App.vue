<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const showLayout = computed(() => {
  return !['/login', '/register'].includes(router.currentRoute.value.path)
})

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div id="app">
    <!-- 顶部导航栏 (登录后显示) -->
    <el-header v-if="showLayout && userStore.isLoggedIn" class="app-header">
      <div class="header-content">
        <div class="logo">
          <h2>气象雷达数据平台</h2>
        </div>
        <el-menu
          :default-active="$route.path"
          mode="horizontal"
          router
          class="nav-menu"
        >
          <el-menu-item index="/dashboard">首页</el-menu-item>
          <el-menu-item index="/sites">站点管理</el-menu-item>
          <el-menu-item index="/data">数据查询</el-menu-item>
          <el-menu-item index="/downloads">下载管理</el-menu-item>
          <el-menu-item index="/images">图片管理</el-menu-item>
        </el-menu>
        <div class="user-actions">
          <el-dropdown>
            <span class="el-dropdown-link">
              <el-icon><User /></el-icon>
              {{ userStore.userInfo.username }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <el-main :class="{ 'with-header': showLayout && userStore.isLoggedIn }">
      <router-view />
    </el-main>
  </div>
</template>

<style scoped>
#app {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

.logo h2 {
  margin: 0;
  color: #409eff;
  font-size: 20px;
  margin-right: 40px;
}

.nav-menu {
  flex: 1;
  border-bottom: none;
}

.user-actions {
  margin-left: 20px;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
}

.with-header {
  padding-top: 20px;
}

.el-main {
  min-height: calc(100vh - 60px);
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>
