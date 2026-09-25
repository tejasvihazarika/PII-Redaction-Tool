import React, { useState, useEffect } from 'react';
import { ShieldCheck, FileText, Upload, Sparkles, Scan, CheckCircle2, XCircle, Download, FileUp, Check, X, Cpu } from 'lucide-react';
import mammoth from 'mammoth';
import { scanTextForPIIAsync, generateRedactedText, checkBackendHealth } from '../services/piiScanner';
import { exportToDocx } from '../services/docxExporter';

const SAMPLE_TICKET_LOG = `================================================================================
TICKET LOG #8401 - RED HERRING PROSPECTUS & SUPPORT AUDIT
================================================================================

Ticket ID: TCK-2026-90412
Date: 2026-09-25 10:14:32
Reporter: Rashi Patil
Email: rashhi.patil@gmail.com
Phone: +91 9876543210
Customer: Rashi Patil
Company: Acme Solutions Pvt Ltd
Address: 17 Market Street, Mumbai, 400001
DOB: 1992-11-05
IP: 192.168.1.105
SSN: 987-65-4321
Credit Card: 4532-7192-8834-1102

Subject: Account access locked after failed payment processing
--------------------------------------------------------------------------------
Issue Summary:
Customer Rashi Patil reported an issue accessing her enterprise dashboard for Acme Solutions Pvt Ltd. 
She attempted a payment renewal using credit card 4532-7192-8834-1102 from IP address 192.168.1.105. 
The system logged a verification failure with SSN 987-65-4321.

Contact Details:
- Alternative Contact: Rohan Dey
- Email: rohan.dey@gmail.com
- Phone: +91 9812345678
- Secondary Address: 452 Elm Street, Suite 300, New York, NY 10001
- Employer: Stark Industries Corp
- Secondary DOB: 1988-04-12
- Server IP: 10.0.4.188`;

export default function Workspace() {
  const [sourceText, setSourceText] = useState("");
  const [fileName, setFileName] = useState("");
  const [outputStyle, setOutputStyle] = useState("fake"); // 'fake' or 'labels'
  const [isScanning, setIsScanning] = useState(false);
  const [findings, setFindings] = useState([]);
  const [hasScanned, setHasScanned] = useState(false);
  const [reviewTab, setReviewTab] = useState("accepted"); // 'accepted' or 'rejected'
  const [backendStatus, setBackendStatus] = useState(null);

  useEffect(() => {
    checkBackendHealth().then(status => {
      setBackendStatus(status);
    });
  }, []);

  const handleScan = async (textToScan = sourceText) => {
    if (!textToScan.trim()) {
      alert("Please upload a document or load a sample first!");
      return;
    }
    setIsScanning(true);
    try {
      const results = await scanTextForPIIAsync(textToScan);
      setFindings(results);
    } catch (err) {
      console.error("Scan error:", err);
    } finally {
      setIsScanning(false);
      setHasScanned(true);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);
    
    if (file.name.endsWith('.docx')) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const arrayBuffer = event.target.result;
        try {
          const result = await mammoth.extractRawText({ arrayBuffer });
          const extractedText = result.value;
          setSourceText(extractedText);
          handleScan(extractedText);
        } catch (err) {
          alert("Error parsing DOCX file: " + err.message);
        }
      };
      reader.readAsArrayBuffer(file);
    } else {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        setSourceText(text);
        handleScan(text);
      };
      reader.readAsText(file);
    }
  };

  const handleLoadSample = () => {
    setSourceText(SAMPLE_TICKET_LOG);
    setFileName("ticket-log.txt");
    handleScan(SAMPLE_TICKET_LOG);
  };

  const setFindingStatus = (id, status) => {
    setFindings(prev => prev.map(f => f.id === id ? { ...f, status } : f));
  };

  const acceptedFindings = findings.filter(f => f.status === "accepted");
  const rejectedFindings = findings.filter(f => f.status === "rejected");
  const uniquePIITypesCount = new Set(acceptedFindings.map(f => f.type)).size;

  const activeRedactedText = generateRedactedText(sourceText, findings, outputStyle);

  const handleDownloadDocx = () => {
    if (!sourceText) return;
    const outName = (fileName || "document").replace(/\.[^/.]+$/, "") + "_redacted.docx";
    exportToDocx(activeRedactedText, outName);
  };

  const handleDownloadTxt = () => {
    if (!sourceText) return;
    const blob = new Blob([activeRedactedText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (fileName || "document").replace(/\.[^/.]+$/, "") + "_redacted.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-200">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold tracking-wider text-emerald-700 uppercase bg-emerald-50 w-fit px-2.5 py-1 rounded border border-emerald-200/60">
            <Scan className="w-3.5 h-3.5" />
            <span>PII ANALYZER / WORKSPACE</span>
          </div>
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight font-sans">
            Make sensitive data safe to share.
          </h1>
          <p className="text-slate-600 text-base max-w-2xl">
            Scan documents and ticket logs for personally identifiable information with SpaCy ML NER and contextual rule engines.
          </p>
        </div>

        {/* Security & Model Status Badge */}
        <div className="flex items-center space-x-3 bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm md:w-80">
          <div className="w-10 h-10 rounded-lg bg-emerald-100/70 flex items-center justify-center text-emerald-700 flex-shrink-0">
            {backendStatus ? <Cpu className="w-6 h-6 text-emerald-600 animate-pulse" /> : <ShieldCheck className="w-6 h-6" />}
          </div>
          <div>
            <div className="text-sm font-bold text-slate-900">
              {backendStatus ? "SpaCy ML Engine Active" : "Private Client Engine"}
            </div>
            <div className="text-xs text-slate-500">
              {backendStatus ? `Model: ${backendStatus.model}` : "Nothing is stored after export"}
            </div>
          </div>
        </div>
      </div>

      {/* Control Bar: Output Style Selector */}
      <div className="flex items-center justify-end gap-4 bg-slate-50/80 p-3 rounded-xl border border-slate-200">
        <div className="flex items-center space-x-3 text-xs font-semibold text-slate-500">
          <span>Output style</span>
          <div className="bg-white p-1 rounded-lg border border-slate-200 flex items-center space-x-1 shadow-xs">
            <button
              onClick={() => setOutputStyle("fake")}
              className={`px-3 py-1 rounded-md text-xs font-bold transition ${
                outputStyle === "fake"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Fake alternatives
            </button>
            <button
              onClick={() => setOutputStyle("labels")}
              className={`px-3 py-1 rounded-md text-xs font-bold transition ${
                outputStyle === "labels"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Labels
            </button>
          </div>
        </div>
      </div>

      {/* STEP 01 / SOURCE MATERIAL */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        
        <div className="flex items-center justify-between">
          <div className="text-xs font-mono font-bold tracking-widest text-slate-400 uppercase">
            01 / SOURCE MATERIAL
          </div>
          {fileName && (
            <span className="text-xs font-mono bg-slate-100 text-slate-700 px-3 py-1 rounded-md font-semibold border border-slate-200">
              {fileName}
            </span>
          )}
        </div>

        <h2 className="text-2xl font-extrabold text-slate-900">
          Drop a prospectus or ticket log
        </h2>

        {/* DOCX Drag & Drop Dropzone Box */}
        <label className="relative border-2 border-dashed border-emerald-300 hover:border-emerald-500 bg-emerald-50/20 hover:bg-emerald-50/40 rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition group">
          <input type="file" accept=".docx,.txt" onChange={handleFileUpload} className="hidden" />
          
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3 group-hover:scale-105 transition shadow-xs">
            <FileUp className="w-6 h-6" />
          </div>

          <div className="text-base font-bold text-slate-900 mb-1">
            Choose a DOCX or TXT file
          </div>
          <div className="text-xs text-slate-500 font-medium">
            or drop it here · max 10 MB
          </div>
        </label>

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-2">
          <button 
            onClick={handleLoadSample}
            className="inline-flex items-center space-x-1.5 text-slate-600 hover:text-slate-900 text-xs font-bold transition px-2 py-1 rounded hover:bg-slate-100"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>✨ Load sample</span>
          </button>

          <button
            onClick={() => handleScan()}
            disabled={isScanning}
            className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white px-6 py-2.5 rounded-xl font-bold text-sm transition shadow-md disabled:opacity-50"
          >
            <Scan className="w-4 h-4 text-emerald-400" />
            <span>{isScanning ? "Scanning with SpaCy..." : "Scan for PII >"}</span>
          </button>
        </div>
      </div>

      {/* STATS BAR */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Findings</div>
          <div className="text-3xl font-extrabold text-slate-900">{acceptedFindings.length}</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">PII Types</div>
          <div className="text-3xl font-extrabold text-emerald-600">{uniquePIITypesCount}</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Review Status</div>
          <div className="text-2xl font-bold text-amber-600">
            {hasScanned ? "Reviewed" : "Waiting"}
          </div>
        </div>

        <div className="bg-emerald-50/60 p-5 rounded-2xl border border-emerald-200/60 flex items-center space-x-3 text-emerald-800">
          <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
          <div className="text-xs font-medium leading-relaxed">
            Manual approval is required before export
          </div>
        </div>

      </div>

      {/* STEP 02 / REVIEW QUEUE */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs font-mono font-bold tracking-widest text-slate-400 uppercase">
              02 / REVIEW QUEUE
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              Detected findings ({findings.length})
            </h2>
          </div>

          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setReviewTab("accepted")}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-2 ${
                reviewTab === "accepted"
                  ? "bg-emerald-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <span>Accepted ({acceptedFindings.length})</span>
            </button>

            <button
              onClick={() => setReviewTab("rejected")}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-2 ${
                reviewTab === "rejected"
                  ? "bg-rose-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <span>Rejected ({rejectedFindings.length})</span>
            </button>
          </div>
        </div>

        {/* Section List: Accepted Findings */}
        {reviewTab === "accepted" && (
          acceptedFindings.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300 text-slate-500 text-sm">
              {hasScanned ? "No accepted findings remaining." : "Run a scan to see detected PII here."}
            </div>
          ) : (
            <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
              {acceptedFindings.map((item) => (
                <div key={item.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white transition hover:bg-slate-50/50">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-200 uppercase font-mono">
                        {item.type.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        Confidence: {(item.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-3 font-mono text-xs pt-1">
                      <span className="text-rose-600 font-medium bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                        Original: "{item.val}"
                      </span>
                      <span className="text-slate-400">→</span>
                      <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        Replacement: "{outputStyle === 'fake' ? (item.replacement_fake || '[REDACTED]') : (item.replacement_tag || `[${item.type.toUpperCase().replace(/\s+/g, '_')}]`)}"
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <button
                      onClick={() => setFindingStatus(item.id, "accepted")}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white shadow-xs flex items-center space-x-1 hover:bg-emerald-700 transition"
                      title="Keep accepted"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Accepted</span>
                    </button>
                    <button
                      onClick={() => setFindingStatus(item.id, "rejected")}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-600 hover:text-white transition flex items-center space-x-1"
                      title="Reject this finding"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Section List: Rejected Findings */}
        {reviewTab === "rejected" && (
          rejectedFindings.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300 text-slate-500 text-sm">
              No findings currently rejected. Click "Reject (✕)" on any finding to move it here.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden bg-rose-50/20">
              {rejectedFindings.map((item) => (
                <div key={item.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/80 transition">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-700 border border-slate-300 uppercase font-mono">
                        {item.type.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-rose-500 font-semibold">
                        [Excluded from Redaction]
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-3 font-mono text-xs pt-1">
                      <span className="text-slate-700 font-medium bg-white px-2 py-0.5 rounded border border-slate-300 line-through">
                        Original: "{item.val}"
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setFindingStatus(item.id, "accepted")}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300 hover:bg-emerald-600 hover:text-white transition flex items-center space-x-1"
                      title="Accept this finding"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Accept</span>
                    </button>
                    <button
                      onClick={() => setFindingStatus(item.id, "rejected")}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 text-white shadow-xs flex items-center space-x-1 hover:bg-rose-700 transition"
                      title="Currently rejected"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Rejected</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

      </div>

      {/* STEP 03 / OUTPUT PREVIEW & EXPORT */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-mono font-bold tracking-widest text-slate-400 uppercase">
              03 / OUTPUT PREVIEW
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              Before & after
            </h2>
          </div>
        </div>

        {/* Side-by-Side Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* ORIGINAL */}
          <div className="space-y-2">
            <div className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">
              ORIGINAL
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 font-mono text-xs text-slate-700 h-64 overflow-y-auto whitespace-pre-wrap custom-scrollbar">
              {sourceText || <span className="text-slate-400">Your source document text will appear here.</span>}
            </div>
          </div>

          {/* REDACTED OUTPUT */}
          <div className="space-y-2">
            <div className="text-xs font-mono font-bold text-emerald-700 uppercase tracking-wider">
              REDACTED OUTPUT ({outputStyle === 'fake' ? 'Fake Alternatives' : 'Labels'})
            </div>
            <div className="bg-emerald-50/40 border border-emerald-200/60 rounded-xl p-4 font-mono text-xs text-emerald-950 h-64 overflow-y-auto whitespace-pre-wrap custom-scrollbar">
              {activeRedactedText || <span className="text-slate-400">Review and apply findings to generate a safe version.</span>}
            </div>
          </div>

        </div>

        {/* Download Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleDownloadDocx}
              disabled={!sourceText}
              className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition shadow-md disabled:opacity-40"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span>Download Redacted DOCX</span>
            </button>

            <button
              onClick={handleDownloadTxt}
              disabled={!sourceText}
              className="inline-flex items-center space-x-2 bg-white text-slate-700 hover:bg-slate-100 border border-slate-300 px-4 py-2.5 rounded-xl text-sm font-semibold transition shadow-xs disabled:opacity-40"
            >
              <Download className="w-4 h-4 text-slate-500" />
              <span>Download TXT</span>
            </button>
          </div>

          <div className="text-xs text-slate-500 font-medium">
            Upload a DOCX to unlock the editable document export
          </div>
        </div>

      </div>

    </div>
  );
}
