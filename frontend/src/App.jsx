import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import "./index.css";

import {
  addMessage,
  setComplaint,
  setError,
  setLoading,
  setRiskAssessment,
  resetComplaint,
} from "./store/complaintSlice";

import {
  analyzeComplaint,
  editComplaint,
  extractComplaintDocument,
  getComplaints,
} from "./services/api";

function App() {
  const dispatch = useDispatch();

  const complaint = useSelector(
    (state) => state.complaint.complaint
  );

  const riskAssessment = useSelector(
    (state) => state.complaint.riskAssessment
  );

  const messages = useSelector(
    (state) => state.complaint.messages
  );

  const loading = useSelector(
    (state) => state.complaint.loading
  );

  const error = useSelector(
    (state) => state.complaint.error
  );
  const refreshComplaints = async () => {
  try {
    const data = await getComplaints();
    setComplaints(data);
  } catch (error) {
    console.error(
      "Failed to refresh complaints:",
      error
    );
  }
};

  const [prompt, setPrompt] = useState("");
  const [complaints, setComplaints] = useState([]);
  const [completeness, setCompleteness] = useState(null);
  const [duplicate, setDuplicate] = useState(null);
  const [capa, setCapa] = useState(null);
useEffect(() => {
  refreshComplaints();
}, []); 
  const fileInputRef = useRef(null);

  const handleNewComplaint = () => {
  dispatch(resetComplaint());
  setPrompt("");
  setCompleteness(null);
  setDuplicate(null);
  setCapa(null);
};
  const handleSelectComplaint = async (selectedComplaint) => {
  try {
    dispatch(setLoading(true));
    dispatch(setError(null));

    const response = await fetch(
      `http://127.0.0.1:8000/api/complaints/${selectedComplaint.id}/analysis`
    );

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(
        data.error || "Unable to load complaint analysis."
      );
    }

    // Complaint
    if (data.complaint) {
      dispatch(setComplaint(data.complaint));
    }

    // Risk Assessment
    if (data.risk_assessment) {
      dispatch(
        setRiskAssessment(data.risk_assessment)
      );
    }

    // Completeness
    setCompleteness(
      data.completeness || null
    );

    // Duplicate Detection
    setDuplicate(
      data.duplicate || null
    );

    // CAPA
    setCapa(
      data.capa || null
    );

    setPrompt("");

  } catch (error) {
    console.error(
      "Failed to load complaint analysis:",
      error
    );

    dispatch(
      setError(
        "Unable to load complaint analysis."
      )
    );

  } finally {
    dispatch(setLoading(false));
  }
};
  const handleSend = async () => {
  if (!prompt.trim() || loading) {
    return;
  }

  const userMessage = prompt.trim();

  const hasExistingComplaint =
    !!(
      complaint.customer_name ||
      complaint.product_name ||
      complaint.batch_number
    );

  dispatch(
    addMessage({
      role: "user",
      content: userMessage,
    })
  );

  setPrompt("");
  dispatch(setLoading(true));
  dispatch(setError(null));

  try {
    let result;

    if (hasExistingComplaint) {
      result = await editComplaint(
        complaint,
        userMessage
      );
    } else {
      setCompleteness(null);
      setDuplicate(null);
      setCapa(null);

      result = await analyzeComplaint(
        userMessage
      );
    }

    console.log("FINAL RESULT:", result);

    if (result?.error) {
      dispatch(setError(result.error));
      return;
    }

    if (result?.complaint) {
      dispatch(
        setComplaint(result.complaint)
      );
    }

    if (result?.risk_assessment) {
      dispatch(
        setRiskAssessment(
          result.risk_assessment
        )
      );
    }

    // Only replace validation panels when the
    // backend actually returned new validation data.
    if (result?.completeness) {
      setCompleteness(result.completeness);
    }

    if (result?.duplicate) {
      setDuplicate(result.duplicate);
    }

    if (result?.capa) {
      setCapa(result.capa);
    }

    dispatch(
      addMessage({
        role: "assistant",
        content: hasExistingComplaint
          ? "I've updated the complaint and refreshed the AI risk assessment."
          : "I've extracted the complaint information and updated the customer complaint form and AI risk assessment.",
      })
    );

    // Refresh history without blocking the UI.
    refreshComplaints().catch((error) => {
      console.error(
        "History refresh failed:",
        error
      );
    });

  } catch (error) {
    console.error(
      "Complaint request error:",
      error
    );

    const detail =
      error.response?.data?.detail;

    const errorMessage = Array.isArray(detail)
      ? detail
          .map((item) => item.msg)
          .join(", ")
      : typeof detail === "string"
        ? detail
        : error.response?.data?.error ||
          "Unable to process the complaint request.";

    dispatch(setError(errorMessage));

  } finally {
    console.log("SETTING LOADING FALSE");
    dispatch(setLoading(false));
  }
};

  const handleFileUpload = async (event) => {
  const file = event.target.files?.[0];

  if (!file) {
    return;
  }

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    dispatch(
      setError("Please upload a PDF file.")
    );
    return;
  }

  setCompleteness(null);
  setDuplicate(null);
  setCapa(null);

  dispatch(setLoading(true));
  dispatch(setError(null));

  dispatch(
    addMessage({
      role: "user",
      content: `Uploaded document: ${file.name}`,
    })
  );

  try {
    const result = await extractComplaintDocument(file);

    if (result.error) {
      dispatch(setError(result.error));
      return;
    }

    if (result.complaint) {
      dispatch(
        setComplaint(result.complaint)
      );
    }

    if (result.risk_assessment) {
      dispatch(
        setRiskAssessment(
          result.risk_assessment
        )
      );
    }

    if (result.completeness) {
      setCompleteness(result.completeness);
    }

    if (result.duplicate) {
      setDuplicate(result.duplicate);
    }

    if (result.capa) {
      setCapa(result.capa);
    }
    await refreshComplaints();

    dispatch(
      addMessage({
        role: "assistant",
        content:
          "I've extracted the complaint information from the document and updated the complaint form and AI analysis.",
      })
    );

  } catch (error) {
    console.error(
      "Document upload error:",
      error
    );

    const detail = error.response?.data?.detail;

    const errorMessage = Array.isArray(detail)
      ? detail
          .map((item) => item.msg)
          .join(", ")
      : typeof detail === "string"
        ? detail
        : "Unable to process the uploaded document.";

    dispatch(setError(errorMessage));

  } finally {
    dispatch(setLoading(false));
    event.target.value = "";
  }
};


  return (
    <div className="app">

      {/* HEADER */}
      <header className="topbar">

        <div className="brand">
          <div className="brand-mark">A</div>

          <div>
            <h1>CMSAI</h1>
            <span>
              Complaint Management System
            </span>
          </div>
        </div>

        <div className="header-actions">

          <button
            className="new-complaint-button"
            onClick={handleNewComplaint}
          >
            + New Complaint
          </button>

          <div className="header-status">
            <span className="status-dot"></span>
            AI Copilot Online
          </div>

        </div>

      </header>


      {/* MAIN WORKSPACE */}
      <main className="workspace">

        {/* ========================= */}
        {/* LEFT COLUMN */}
        {/* ========================= */}

        <div className="left-column">
          {/* COMPLAINT HISTORY */}
<section className="panel history-panel">

  <div className="panel-header">
    <div>
      <span className="eyebrow">HISTORY</span>
      <h2>Previous Complaints</h2>
    </div>

    <span className="history-count">
      {complaints.length}
    </span>
  </div>

  <div className="history-list">

    {complaints.length === 0 ? (
      <div className="history-empty">
        No previous complaints
      </div>
    ) : (
      complaints.map((item) => (
        <div
          className="history-item"
          key={item.id}
          onClick={() => handleSelectComplaint(item)}
        >

          <div className="history-main">

            <strong>
              {item.customer_name || "Unknown Customer"}
            </strong>

            <span>
              {item.product_name || "Unknown Product"}
            </span>

            <small>
              Batch: {item.batch_number || "—"}
            </small>

          </div>

          <div className="history-risk">
            <span>
              {item.complaint_type || "Complaint"}
            </span>

            <strong>
              {item.risk_level || "—"}
            </strong>
          </div>

        </div>
      ))
    )}

  </div>

</section>

          {/* CUSTOMER COMPLAINT */}
          <section className="panel complaint-panel">

            <div className="panel-header">

              <div>
                <span className="eyebrow">
                  CUSTOMER COMPLAINT
                </span>

                <h2>
                  Log Customer Complaint
                </h2>
              </div>

              <span className="ai-badge">
                AI Assisted
              </span>

            </div>


            <div className="form-grid">

              <div className="field">
                <label>Customer Name</label>

                <input
                  value={
                    complaint.customer_name || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>Customer Email</label>

                <input
                  value={
                    complaint.customer_email || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>Product Name</label>

                <input
                  value={
                    complaint.product_name || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>
                  Product Strength / Grade
                </label>

                <input
                  value={
                    complaint.product_strength || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>Batch / Lot Number</label>

                <input
                  value={
                    complaint.batch_number || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>Quantity Affected</label>

                <input
                  value={
                    complaint.quantity_affected || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>Manufacturing Date</label>

                <input
                  value={
                    complaint.manufacturing_date || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field">
                <label>
                  Expiry / Retest Date
                </label>

                <input
                  value={
                    complaint.expiry_date || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field full-width">
                <label>Complaint Type</label>

                <input
                  value={
                    complaint.complaint_type || ""
                  }
                  placeholder="Waiting for AI..."
                  readOnly
                />
              </div>


              <div className="field full-width">
                <label>
                  Complaint Description
                </label>

                <textarea
                  value={
                    complaint.complaint_description || ""
                  }
                  placeholder="Complaint details will appear here..."
                  readOnly
                />
              </div>

            </div>

          </section>
          


          {/* RISK ASSESSMENT */}

<section className="panel risk-panel">

  <div className="panel-header">
    <div>
      <span className="eyebrow">
        AI ANALYSIS
      </span>

      <h2>
        Risk Assessment
      </h2>
    </div>

    <span className="risk-placeholder">
      {riskAssessment?.risk_level
        ? "AI assessment complete"
        : "Awaiting complaint"}
    </span>
  </div>

  <div className="risk-section">

    <div className="risk-grid">

      <div className="risk-card">
        <span>Severity</span>
        <strong>
          {riskAssessment?.severity || "—"}
        </strong>
      </div>

      <div className="risk-card">
        <span>Priority</span>
        <strong>
          {riskAssessment?.priority || "—"}
        </strong>
      </div>

      <div className="risk-card">
        <span>Risk Level</span>
        <strong>
          {riskAssessment?.risk_level || "—"}
        </strong>
      </div>

    </div>

    <div className="recommendation">

      <span>
        Recommended Action
      </span>

      <p>
        {riskAssessment?.recommended_action ||
          "AI recommendation will appear here."}
      </p>

      {riskAssessment?.reasoning && (
        <>
          <span className="risk-reasoning-label">
            AI Reasoning
          </span>

          <p>
            {riskAssessment.reasoning}
          </p>
        </>
      )}

      {Array.isArray(
        riskAssessment?.recommendations
      ) &&
        riskAssessment.recommendations.length > 0 && (
          <>
            <span className="risk-reasoning-label">
              Recommendations
            </span>

            <ul className="recommendations-list">
              {riskAssessment.recommendations.map(
                (recommendation, index) => (
                  <li key={index}>
                    {recommendation}
                  </li>
                )
              )}
            </ul>
          </>
        )}

    </div>

  </div>

</section>


{/* COMPLAINT COMPLETENESS */}

<section className="panel completeness-panel">

  <div className="panel-header">

    <div>
      <span className="eyebrow">
        AI VALIDATION
      </span>

      <h2>
        Complaint Completeness
      </h2>
    </div>

    {completeness && (
      <span className="completeness-score">
        {completeness.score}%
      </span>
    )}

  </div>

  {!completeness ? (

    <div className="completeness-empty">
      Completeness check will appear after
      analyzing a complaint.
    </div>

  ) : (

    <div className="completeness-content">

      <div className="completeness-summary">

        <strong>
          {completeness.completed} / {completeness.total}
        </strong>

        <span>
          required sections complete
        </span>

      </div>

      <div className="completeness-list">

        {completeness.checks?.map(
          (check, index) => (

            <div
              className="completeness-item"
              key={index}
            >

              <span
                className={
                  check.complete
                    ? "check-icon complete"
                    : "check-icon missing"
                }
              >
                {check.complete ? "✓" : "!"}
              </span>

              <span>
                {check.category}
              </span>

            </div>

          )
        )}

      </div>

      {completeness.missing?.length > 0 && (

        <div className="missing-fields">

          <span>
            Missing Information
          </span>

          <p>
            {completeness.missing.join(", ")}
          </p>

        </div>

      )}

    </div>

  )}

</section>


{/* DUPLICATE DETECTION */}

<section className="panel duplicate-panel">

  <div className="panel-header">

    <div>
      <span className="eyebrow">
        AI VALIDATION
      </span>

      <h2>
        Duplicate Detection
      </h2>
    </div>

    {duplicate && (
      <span
        className={
          duplicate.is_duplicate
            ? "duplicate-badge warning"
            : "duplicate-badge clear"
        }
      >
        {duplicate.is_duplicate
          ? "Possible Duplicate"
          : "No Duplicate"}
      </span>
    )}

  </div>

  {!duplicate ? (

    <div className="duplicate-empty">
      Duplicate check will appear after analyzing
      a complaint.
    </div>

  ) : duplicate.is_duplicate ? (

    <div className="duplicate-content">

      <div className="duplicate-warning">

        <strong>
          Possible duplicate complaint detected
        </strong>

        <p>
          A similar complaint already exists in
          the complaint database.
        </p>

      </div>

      <div className="duplicate-details">

        <div>
          <span>Complaint ID</span>
          <strong>
            #{duplicate.complaint_id}
          </strong>
        </div>

        <div>
          <span>Customer</span>
          <strong>
            {duplicate.customer_name || "—"}
          </strong>
        </div>

        <div>
          <span>Product</span>
          <strong>
            {duplicate.product_name || "—"}
          </strong>
        </div>

        <div>
          <span>Batch</span>
          <strong>
            {duplicate.batch_number || "—"}
          </strong>
        </div>

      </div>

      <div className="duplicate-reason">

        <span>
          Reason
        </span>

        <p>
          {duplicate.reason}
        </p>

      </div>

    </div>

  ) : (

    <div className="duplicate-clear">
      ✓ No matching previous complaint was found.
    </div>

  )}

</section>


{/* CAPA */}

<section className="panel capa-panel">

  <div className="panel-header">

    <div>
      <span className="eyebrow">
        AI QUALITY ASSURANCE
      </span>

      <h2>
        CAPA Recommendation
      </h2>
    </div>

    {capa && (
      <span className="capa-badge">
        {capa.priority || "High"} Priority
      </span>
    )}

  </div>

  {!capa ? (

    <div className="capa-empty">
      CAPA recommendations will appear after
      complaint analysis.
    </div>

  ) : (

    <div className="capa-content">

      <div className="capa-section">

        <span>
          Corrective Action
        </span>

        <p>
          {capa.corrective_action}
        </p>

      </div>

      <div className="capa-section">

        <span>
          Preventive Action
        </span>

        <p>
          {capa.preventive_action}
        </p>

      </div>

      <div className="capa-meta">

        <div>
          <span>
            Investigation Required
          </span>

          <strong>
            {capa.investigation_required
              ? "Yes"
              : "No"}
          </strong>
        </div>

        <div>
          <span>
            Priority
          </span>

          <strong>
            {capa.priority || "—"}
          </strong>
        </div>

      </div>

      <div className="capa-reasoning">

        <span>
          AI Reasoning
        </span>

        <p>
          {capa.reasoning}
        </p>

      </div>

      <div className="capa-disclaimer">
        AI-generated recommendation — requires
        review and approval by qualified QA personnel.
      </div>

    </div>

  )}

</section>

        </div>


        {/* ========================= */}
        {/* RIGHT COLUMN - COPILOT */}
        {/* ========================= */}

        <section className="panel copilot-panel">

          <div className="panel-header">

            <div>

              <span className="eyebrow">
                AI ASSISTANT
              </span>

              <h2>
                CMSAI Copilot
              </h2>

            </div>

            <div className="copilot-icon">
              ✦
            </div>

          </div>


          {/* CHAT */}
          <div className="chat-area">

            {messages.length === 0 ? (

              <div className="welcome-message">

                <div className="assistant-avatar">
                  ✦
                </div>

                <div>

                  <strong>
                    How can I help?
                  </strong>

                  <p>
                    Describe a customer complaint
                    or upload a complaint document.
                    I'll extract the information and
                    populate the complaint form for you.
                  </p>

                </div>

              </div>

            ) : (

              <div className="messages">

                {messages.map(
                  (message, index) => (

                    <div
                      key={index}
                      className={`message ${
                        message.role === "user"
                          ? "user-message"
                          : "assistant-message"
                      }`}
                    >

                      <div className="message-label">
                        {message.role === "user"
                          ? "You"
                          : "CMSAI Copilot"}
                      </div>

                      <div className="message-content">
                        {message.content}
                      </div>

                    </div>

                  )
                )}

              </div>

            )}


            {loading && (

              <div className="assistant-message">

                <div className="message-label">
                  CMSAI Copilot
                </div>

                <div className="message-content">
                  Analyzing complaint...
                </div>

              </div>

            )}

          </div>


          {/* COMPOSER */}
          <div className="composer">

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <textarea
              placeholder="Describe the customer complaint..."
              rows="2"
              value={prompt}
              onChange={(event) =>
                setPrompt(event.target.value)
              }
              onKeyDown={(event) => {

                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {

                  event.preventDefault();
                  handleSend();

                }

              }}
            />


            <div className="composer-actions">

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileUpload}
                style={{
                  display: "none",
                }}
              />


              <button
                className="upload-button"
                onClick={() =>
                  fileInputRef.current?.click()
                }
                disabled={loading}
              >
                ＋ Upload PDF
              </button>


              <button
                className="send-button"
                onClick={handleSend}
                disabled={
                  loading ||
                  !prompt.trim()
                }
              >
                {loading
                  ? "Analyzing..."
                  : "Send"}
              </button>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;