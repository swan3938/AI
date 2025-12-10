import { createApp } from "vue";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import Upload from "./pages/Upload.vue";

const app = createApp(Upload);
app.use(ElementPlus);
app.mount("#app");
