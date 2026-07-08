'use client';

import { useEffect, useState } from 'react';
import styles from './page.module.css';

type RawRule = {
  id: string;
  parameter: string;
  operator: string;
  value: any;
};

type AuditScheme = {
  id: string;
  name: string;
  provider: string;
  description: string;
  eligibility_requirements: string[];
  raw_eligibility_rules: RawRule[];
  questions_to_ask: string[];
  steps_to_apply: string[];
  urls: string[];
  full_document: any;
};

const RULE_PARAMETERS = [
  "business.msme_segment",
  "business.turnover",
  "business.state",
  "business.district",
  "business.sector",
  "business.ownership_category",
  "business.constitution",
  "business.investment_plant_machinery",
  "business.establishment_year",
  "business.has_udyam_registration",
  "business.employment_count",
  "business.export_status"
];

const RULE_OPERATORS = ["=", "!=", ">", "<", ">=", "<=", "IN", "NOT IN", "BETWEEN", "CONTAINS"];

function SchemeCard({ scheme, onSaveRules, onSaveScheme }: { scheme: AuditScheme, onSaveRules: (id: string, rules: RawRule[]) => void, onSaveScheme: (id: string, document: any) => void }) {
  const [rules, setRules] = useState<RawRule[]>(scheme.raw_eligibility_rules || []);
  const [newParam, setNewParam] = useState(RULE_PARAMETERS[0]);
  const [newOp, setNewOp] = useState(RULE_OPERATORS[0]);
  const [newVal, setNewVal] = useState("");
  const [isSavingRules, setIsSavingRules] = useState(false);
  const [isSavingDoc, setIsSavingDoc] = useState(false);
  const [isJsonOpen, setIsJsonOpen] = useState(false);
  const [jsonStr, setJsonStr] = useState(JSON.stringify(scheme.full_document, null, 2));
  const [jsonError, setJsonError] = useState("");

  const handleAddRule = () => {
    if (!newVal.trim()) return;
    
    // Parse value string to appropriate type based on heuristics
    let parsedVal: any = newVal;
    if (newVal.toLowerCase() === 'true') parsedVal = true;
    else if (newVal.toLowerCase() === 'false') parsedVal = false;
    else if (!isNaN(Number(newVal))) parsedVal = Number(newVal);
    else if (newVal.startsWith('[') && newVal.endsWith(']')) {
        try {
            // Very hacky array parsing for IN operator
            parsedVal = newVal.slice(1,-1).split(',').map(s => s.trim().replace(/^['"](.*)['"]$/, '$1'));
        } catch(e) {}
    }

    setRules([...rules, { id: "RULE_" + Date.now(), parameter: newParam, operator: newOp, value: parsedVal }]);
    setNewVal("");
  };

  const handleDeleteRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  const handleSaveRules = async () => {
    setIsSavingRules(true);
    await onSaveRules(scheme.id, rules);
    setIsSavingRules(false);
  };

  const handleSaveJson = async () => {
    try {
      const parsed = JSON.parse(jsonStr);
      setJsonError("");
      setIsSavingDoc(true);
      await onSaveScheme(scheme.id, parsed);
      setIsSavingDoc(false);
    } catch (e: any) {
      setJsonError(e.message || "Invalid JSON syntax");
    }
  };

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <h2 className={styles.schemeName}>{scheme.name}</h2>
        <span className={styles.provider}>{scheme.provider}</span>
      </div>
      
      <p className={styles.description}>{scheme.description || "No description provided."}</p>

      {scheme.urls && scheme.urls.length > 0 && (
        <div className={styles.section}>
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
            URLs
          </h3>
          <ul className={styles.list}>
            {scheme.urls.map((u, i) => (
              <li key={i} className={styles.listItem}>
                <a href={u} target="_blank" rel="noopener noreferrer" className={styles.urlLink}>{u}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.section}>
        <h3>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          Eligibility Rules
        </h3>
        {rules.length > 0 ? (
          <ul className={styles.list}>
            {rules.map((req, i) => (
              <li key={i} className={styles.listItem}>
                <code>{req.parameter} {req.operator} {JSON.stringify(req.value)}</code>
                <button className={styles.deleteBtn} onClick={() => handleDeleteRule(i)}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className={styles.emptyState}>No hardcoded rules.</p>
        )}

        <div className={styles.editForm}>
          <select className={styles.select} value={newParam} onChange={e => setNewParam(e.target.value)}>
            {RULE_PARAMETERS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className={styles.select} value={newOp} onChange={e => setNewOp(e.target.value)}>
            {RULE_OPERATORS.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
          <input className={styles.input} placeholder="Value (e.g. 50000 or ['micro'])" value={newVal} onChange={e => setNewVal(e.target.value)} />
          <button className={styles.button} onClick={handleAddRule}>Add</button>
        </div>

        <button className={`${styles.button} ${styles.saveBtn}`} onClick={handleSaveRules} disabled={isSavingRules}>
          {isSavingRules ? "Saving & Recompiling..." : "Save Rules"}
        </button>
      </div>

      <div className={styles.section}>
        <h3>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          AI Questions
        </h3>
        {scheme.questions_to_ask && scheme.questions_to_ask.length > 0 ? (
          <ul className={styles.list}>
            {scheme.questions_to_ask.map((q, i) => (
              <li key={i} className={styles.listItem}>{q}</li>
            ))}
          </ul>
        ) : (
          <p className={styles.emptyState}>No specific questions mapped.</p>
        )}
      </div>
      
      <div className={styles.section}>
        <h3>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          Application Workflow
        </h3>
        {scheme.steps_to_apply && scheme.steps_to_apply.length > 0 ? (
          <ul className={styles.list}>
            {scheme.steps_to_apply.map((step, i) => (
              <li key={i} className={styles.listItem}>{i + 1}. {step}</li>
            ))}
          </ul>
        ) : (
          <p className={styles.emptyState}>No workflow steps defined.</p>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.jsonHeader} onClick={() => setIsJsonOpen(!isJsonOpen)}>
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
            Advanced Schema Editor (JSON)
          </h3>
          <span>{isJsonOpen ? "▼" : "▶"}</span>
        </div>
        {isJsonOpen && (
          <div className={styles.jsonEditorContainer}>
            <p className={styles.description}>Edit the raw schema directly. This includes all tags, benefits, requirements, and metadata.</p>
            <textarea 
              className={styles.jsonTextarea} 
              value={jsonStr} 
              onChange={e => setJsonStr(e.target.value)}
              spellCheck={false}
            />
            {jsonError && <p className={styles.errorText}>{jsonError}</p>}
            <button className={`${styles.button} ${styles.saveBtn}`} onClick={handleSaveJson} disabled={isSavingDoc}>
              {isSavingDoc ? "Validating & Saving..." : "Save Full Document"}
            </button>
          </div>
        )}
      </div>

    </div>
  );
}

export default function AuditPage() {
  const [schemes, setSchemes] = useState<AuditScheme[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAuditData = async () => {
    try {
      const res = await fetch('/api/audit/schemes');
      const data = await res.json();
      setSchemes(data);
    } catch (error) {
      console.error("Failed to fetch audit data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  const handleSaveRules = async (schemeId: string, rules: RawRule[]) => {
    try {
      const res = await fetch(`/api/scheme/${schemeId}/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rules })
      });
      if (res.ok) {
        // Refresh the whole dashboard to reflect new questions compiled
        await fetchAuditData();
      } else {
        alert("Failed to save rules.");
      }
    } catch (err) {
      console.error(err);
      alert("Error saving rules.");
    }
  const handleSaveScheme = async (schemeId: string, document: any) => {
    try {
      const res = await fetch(`/api/scheme/${schemeId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document })
      });
      if (res.ok) {
        await fetchAuditData();
        alert("Document saved successfully!");
      } else {
        const errorData = await res.json();
        alert("Failed to save document: " + (errorData.detail || "Unknown error"));
      }
    } catch (err) {
      console.error(err);
      alert("Error saving document.");
    }
  };

  if (loading) {
    return (
      <div className={styles.auditContainer}>
        <div className={styles.header}>
          <h1>Scheme Audit Dashboard</h1>
          <p>Loading scheme rules...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.auditContainer}>
      <div className={styles.header}>
        <h1>Scheme Audit Dashboard</h1>
        <p>Review all indexed government schemes, their programmatic eligibility rules, and the questions the AI will ask.</p>
      </div>

      <div className={styles.grid}>
        {schemes.map((scheme) => (
          <SchemeCard key={scheme.id} scheme={scheme} onSaveRules={handleSaveRules} onSaveScheme={handleSaveScheme} />
        ))}
      </div>
    </div>
  );
}
