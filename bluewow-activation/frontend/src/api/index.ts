import axios from "axios";
const base = (import.meta as any).env?.VITE_API_BASE || "/";
export const api = axios.create({ baseURL: base });
