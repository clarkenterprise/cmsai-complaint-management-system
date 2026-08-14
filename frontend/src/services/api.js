import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function analyzeComplaint(message) {
  const response = await api.post("/api/complaints/analyze", {
    message,
  });

  return response.data;
}

export async function editComplaint(currentComplaint, update) {
  const complaint = { ...currentComplaint };

  const dateFields = [
    "manufacturing_date",
    "expiry_date",
    "complaint_date",
  ];

  dateFields.forEach((field) => {
    const value = complaint[field];

    if (!value) return;

    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return;
    }

    const match = value.match(
      /^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/
    );

    if (match) {
      const [, day, month, year] = match;

      const months = {
        Jan: "01",
        Feb: "02",
        Mar: "03",
        Apr: "04",
        May: "05",
        Jun: "06",
        Jul: "07",
        Aug: "08",
        Sep: "09",
        Oct: "10",
        Nov: "11",
        Dec: "12",
      };

      complaint[field] =
        `${year}-${months[month]}-${day.padStart(2, "0")}`;
    }
  });

  console.log("EDIT REQUEST:", {
    current_complaint: complaint,
    update,
  });

  const response = await api.post(
    "/api/complaints/edit",
    {
      current_complaint: complaint,
      update,
    }
  );

  console.log("EDIT RESPONSE:", response.data);

  return response.data;
}
export async function extractComplaintDocument(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await axios.post(
    `${API_BASE_URL}/api/complaints/extract-document`,
    formData
  );

  return response.data;
}

export async function getComplaints() {
  const response = await api.get("/api/complaints");

  return response.data;
}
