import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/books',
    name: 'books',
    component: () => import(/* webpackChunkName: "books" */ '../views/book/ListView.vue')
  },
  {
    path: '/book/:id',
    name: 'book',
    component: () => import(/* webpackChunkName: "book" */ '../views/book/DetailView.vue'),
    props: true
  },
  {
    path: '/words',
    name: 'words',
    component: () => import(/* webpackChunkName: "words" */ '../views/word/ListView.vue')
  },
  {
    path: '/word/search',
    name: 'wordSearch',
    component: () => import(/* webpackChunkName: "words" */ '../views/word/SearchView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
