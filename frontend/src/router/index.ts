import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表板', icon: 'Odometer' }
      },
      {
        path: 'sites',
        name: 'Sites',
        component: () => import('../views/Sites/index.vue'),
        meta: { title: '站点管理', icon: 'Location' }
      },
      {
        path: 'sites/:id',
        name: 'SiteDetail',
        component: () => import('../views/Sites/Detail.vue'),
        meta: { title: '站点详情', hidden: true }
      },
      {
        path: 'data/query',
        name: 'DataQuery',
        component: () => import('../views/Data/Query.vue'),
        meta: { title: '数据查询', icon: 'DataLine' }
      },
      {
        path: 'prediction',
        name: 'Prediction',
        component: () => import('../views/Prediction/index.vue'),
        meta: { title: '预测分析', icon: 'TrendCharts' }
      },
      {
        path: 'download/management',
        name: 'DownloadManagement',
        component: () => import('../views/Download/Management.vue'),
        meta: { title: '下载管理', icon: 'Download' }
      },
      {
        path: 'system/monitor',
        name: 'SystemMonitor',
        component: () => import('../views/System/Monitor.vue'),
        meta: { title: '系统监控', icon: 'Monitor' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '404' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = userStore.isAuthenticated

  // 设置页面标题
  document.title = to.meta.title
    ? `${to.meta.title} - 气象雷达数据平台`
    : '气象雷达数据管理与预测平台'

  // 检查是否需要认证
  if (to.meta.requiresAuth !== false && !isAuthenticated) {
    ElMessage.warning('请先登录')
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
