import axios from "axios";

/**
 * Axios instance
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
  timeout: 15000,
});

/**
 * List vehicle logs (pagination + filters)
 */
export async function listVehicleLogs({
  search = "",
  date_from,
  date_to,
  limit = 10,
  offset = 0,
} = {}) {
  const res = await api.get("/api/vehicle-logs/", {
    params: {
      search: search || undefined,
      date_from: date_from || undefined,
      date_to: date_to || undefined,
      limit,
      offset,
    },
  });
  return res.data;
}

// import axios from "axios";

// /**
//  * Axios instance
//  * Adjust baseURL if needed
//  */
// const api = axios.create({
//   baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
//   timeout: 15000,
// });

// /**
//  * List vehicle logs
//  */
// export async function listVehicleLogs(params = {}) {
//   const res = await api.get("api/vehicle-logs", {
//     params,
//   });
//   return res.data;
// }
