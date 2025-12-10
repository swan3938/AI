<template>
  <div style="padding:16px">
    <h2>上传登录/激活名单</h2>
    <el-upload :auto-upload="true" :http-request="uploadActivation" accept=".csv,.xlsx">
      <el-button>上传激活名单</el-button>
    </el-upload>
    <el-button type="primary" style="margin-left:12px" @click="process">生成报告</el-button>
    <el-divider />
    <el-space direction="vertical" style="width:100%">
      <el-card v-if="overview">
        <div>总激活人数：{{ overview.activated }}</div>
      </el-card>
      <el-card>
        <div style="display:flex;gap:16px;align-items:center">
          <el-button @click="download('monthly')">下载月度CSV</el-button>
          <el-button @click="download('subject')">下载主体总体CSV</el-button>
          <el-button @click="download('activated')">下载激活明细CSV</el-button>
        </div>
      </el-card>
      <el-card>
        <div>月度激活人数</div>
        <div ref="monthlyRef" style="width:100%;height:360px"></div>
      </el-card>
      <el-card>
        <div>主体总体分布</div>
        <div ref="subjectRef" style="width:100%;height:360px"></div>
      </el-card>
    </el-space>
    <el-dialog v-model="rawVisible" title="原始数据" width="80%">
      <el-table :data="rawRows" style="width:100%">
        <el-table-column prop="employee_id" label="工号" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="company" label="公司" />
        <el-table-column prop="subject" label="主体" />
        <el-table-column prop="platform" label="平台" />
        <el-table-column prop="first_login_at" label="首次登录时间" />
      </el-table>
    </el-dialog>
  </div>
</template>
<script lang="ts" setup>
import { api } from "../api/index";
import { ref, watch } from "vue";
import * as echarts from "echarts";
const overview = ref<any>(null);
const monthly = ref<any[]>([]);
const subjectOverall = ref<any[]>([]);
const monthlyRef = ref();
const subjectRef = ref();
let monthlyChart: any = null;
let subjectChart: any = null;
const rawVisible = ref(false);
const rawRows = ref<any[]>([]);

const uploadActivation = async (opt: any) => {
  const fd = new FormData();
  fd.append("file", opt.file);
  const { data } = await api.post("/api/bluewow/upload/activation", fd);
  overview.value = null;
  opt.onSuccess(data);
};
const process = async () => {
  const { data } = await api.post("/api/bluewow/process");
  overview.value = data.overview;
  monthly.value = data.monthly || [];
  subjectOverall.value = data.subject_overall || [];
};
const download = (which: string) => {
  if (which === "monthly") window.open("/api/bluewow/download/monthly.csv", "_blank");
  else if (which === "subject") window.open("/api/bluewow/download/subject_overall.csv", "_blank");
  else window.open("/api/bluewow/download/activated.csv", "_blank");
};
const showRawByMonth = async (m: string) => {
  const { data } = await api.get("/api/bluewow/raw", { params: { month: m } });
  rawRows.value = data;
  rawVisible.value = true;
};
const showRawBySubject = async (s: string) => {
  const { data } = await api.get("/api/bluewow/raw", { params: { subject: s } });
  rawRows.value = data;
  rawVisible.value = true;
};
watch(monthly, (val) => {
  if (!monthlyRef.value) return;
  if (!monthlyChart) monthlyChart = echarts.init(monthlyRef.value);
  const x = val.map((i: any) => i.month);
  const y = val.map((i: any) => i.activated);
  monthlyChart.setOption({
    tooltip: {},
    xAxis: { type: "category", data: x },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: y }]
  });
  monthlyChart.off("click");
  monthlyChart.on("click", (params: any) => showRawByMonth(params.name));
});
watch(subjectOverall, (val) => {
  if (!subjectRef.value) return;
  if (!subjectChart) subjectChart = echarts.init(subjectRef.value);
  subjectChart.setOption({
    tooltip: {},
    series: [{ type: "pie", radius: "60%", data: val.map((i: any) => ({ name: i.subject, value: i.count })) }]
  });
  subjectChart.off("click");
  subjectChart.on("click", (params: any) => showRawBySubject(params.name));
});
</script>
