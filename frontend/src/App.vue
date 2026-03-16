<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()

onMounted(() => {
  // 初始化用户信息
  userStore.loadUserFromStorage()
})
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
}
</style>
