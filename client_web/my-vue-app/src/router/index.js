import Vue from "vue";
import VueRouter from "vue-router";

Vue.use(VueRouter);
const routes = [
  {
    path: "/",
    name: "HomepageMerged",
    component: () => import("../components/home/HomepageMerged.vue"),
    meta: {
      authRequired: false,
    },
  },
];
const router = new VueRouter({
    mode:'history',
    routes
})
export default router