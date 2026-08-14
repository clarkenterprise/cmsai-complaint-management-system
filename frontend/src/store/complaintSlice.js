import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  complaint: {
    complaint_source: "",
    customer_name: "",
    customer_email: "",
    product_name: "",
    product_strength: "",
    batch_number: "",
    manufacturing_date: "",
    expiry_date: "",
    quantity_affected: "",
    complaint_type: "",
    complaint_date: "",
    complaint_description: "",
  },

  riskAssessment: {
    severity: "",
    priority: "",
    risk_level: "",
    reasoning: "",
    recommended_action: "",
    recommendations: [],
  },

  messages: [],

  loading: false,

  error: null,
};

const complaintSlice = createSlice({
  name: "complaint",
  initialState,

  reducers: {
    setComplaint(state, action) {
      state.complaint = {
        ...state.complaint,
        ...action.payload,
      };
    },

    setRiskAssessment(state, action) {
      state.riskAssessment = {
        ...state.riskAssessment,
        ...action.payload,
      };
    },

    addMessage(state, action) {
      state.messages.push(action.payload);
    },

    setLoading(state, action) {
      state.loading = action.payload;
    },

    setError(state, action) {
      state.error = action.payload;
    },

    clearError(state) {
      state.error = null;
    },

   resetComplaint(state) {
  state.complaint = { ...initialState.complaint };
  state.riskAssessment = {
    ...initialState.riskAssessment,
    recommendations: [],
  };
  state.messages = [];
  state.loading = false;
  state.error = null;
},
  },
});

export const {
  setComplaint,
  setRiskAssessment,
  addMessage,
  setLoading,
  setError,
  clearError,
  resetComplaint,
} = complaintSlice.actions;

export default complaintSlice.reducer;