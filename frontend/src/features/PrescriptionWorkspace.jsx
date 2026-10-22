import React,{useEffect,useMemo,useState} from 'react';
import { AlertTriangle, ArrowLeft, BookOpen, Check, ChevronDown, ClipboardCheck, Download, Eye, FileText, LoaderCircle, ShieldAlert, ShieldCheck, Trash2 } from 'lucide-react';
import {Badge,EmptyState,Notice} from '../components/Status.jsx';
import ImageEvidence from '../components/ImageEvidence.jsx';
import FindingsCenter from '../components/FindingsCenter.jsx';
import {confirmTranscription,formatEngine,request,saveJSON} from '../lib/api.js';
import {ageLabel,comparisonLabel,doseLabel} from '../lib/screeningLabels.js';
export default function PrescriptionWorkspace({detail,onReviewed,onDeleted}){
 const [editing,setEditing]=useState(false),[audit,setAudit]=useState([]);
 const [transcript,setTranscript]=useState(''),[tab,setTab]=useState('transcription'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[references,setReferences]=useState({}),[openReference,setOpenReference]=useState({}),[labels,setLabels]=useState({});
 useEffect(()=>{setTranscript(detail?.corrected_text||detail?.original_text||'');setTab(detail?.reviewer_confirmed?'findings':'transcription');setError('');setReferences({});setLabels({});setEditing(false)},[detail?.id,detail?.reviewer_confirmed]);
 useEffect(()=>{if(!detail?.id)return;let active=true;request('/prescriptions/'+encodeURIComponent(detail.id)+'/audit').then(v=>{if(active)setAudit(v.events||[])}).catch(()=>{if(active)setAudit([])});return()=>{active=false}},[detail?.id,detail?.updated]);
 const report=detail?.report||{},medications=report.medications||[],issues=report.issues||[];
 const reviewed=!!detail?.reviewer_confirmed;
 const verify=async()=>{if(!transcript.trim()){setError('Review and correct the transcription before confirming.');return}setBusy(true);setError('');
  try{await confirmTranscription(detail.id,transcript);setEditing(false);await onReviewed()}catch(e){setError(e.message)}finally{setBusy(false)}};
 const remove=async()=>{if(!window.confirm('Permanently delete this prescription and image?'))return;setBusy(true);try{await request('/prescriptions/'+encodeURIComponent(detail.id),{method:'DELETE'});await onDeleted()}catch(e){setError(e.message)}finally{setBusy(false)}};
 const lookup=async(name)=>{if(!name||references[name])return;setOpenReference(o=>({...o,[name]:true}));
  try{const value=await request('/reference?medicine='+encodeURIComponent(name));setReferences(r=>({...r,[name]:value}))}catch(e){setReferences(r=>({...r,[name]:{status:'REFERENCE_UNAVAILABLE',reason:e.message}}))}};
 const viewLabel=async(setid)=>{if(!setid||['LOADING','UNVERIFIED_LABEL_EVIDENCE'].includes(labels[setid]?.status))return;setLabels(v=>({...v,[setid]:{status:'LOADING'}}));
  try{const value=await request('/reference/label/'+encodeURIComponent(setid));setLabels(v=>({...v,[setid]:value}))}catch(e){setLabels(v=>({...v,[setid]:{status:'UNAVAILABLE',reason:e.message}}))}};
 if(!detail)return <EmptyState icon={FileText} title="No prescription selected" description="Open a prescription from records to begin."/>;
 return <div className="stack-lg">
  <div className="review-heading"><div className="review-file-icon"><FileText size={23}/></div><div><h2>{detail.filename}</h2><p>Analysis ID · {detail.id.slice(0,8)} · {formatEngine(detail.engine)}</p></div>
   <Badge tone={reviewed?'teal':'amber'}>{reviewed?'Text checked':'Check text'}</Badge>
   <button className="button button-ghost review-export" onClick={()=>saveJSON('medsafe-'+detail.id.slice(0,8)+'.json',detail)}><Download size={17}/> Export report</button></div>
  <div className="workflow-progress"><div className="workflow-stage is-complete"><span><Check size={14}/></span><strong>01 · Read image</strong></div>
   <div className={'workflow-stage '+(reviewed?'is-complete':'is-current')}><span>{reviewed?<Check size={14}/>:2}</span><strong>02 · Check text</strong></div>
   <div className={'workflow-stage '+(reviewed?'is-current':'is-upcoming')}><span>3</span><strong>03 · View findings</strong></div></div>
  <div className="review-grid">
   <section className="surface preview-surface"><div className="section-top"><div><h3>Original prescription</h3><p>Source image for manual cross-checking</p></div><Eye size={19} className="muted-icon"/></div>
     <div className="preview-frame"><ImageEvidence src={detail.image_url}
       width={detail.ocr?.width} height={detail.ocr?.height}
       regions={detail.ocr?.regions||[]} alt="Uploaded prescription; compare against OCR text"/></div>
     {detail.ocr?.preprocessing?.quality?.warnings?.length>0&&<div className="image-quality-flags">
      <strong>Image quality</strong>
      {detail.ocr.preprocessing.quality.warnings.map((warning,i)=><span key={i}>{warning.replaceAll('_',' ')}</span>)}
     </div>}
     <div className="preview-footer"><span>Read with <strong>{formatEngine(detail.engine)}</strong>{detail.ocr?.processing_seconds!=null?' · '+detail.ocr.processing_seconds+' seconds':''}</span><Badge tone="amber">Check against image</Badge></div>
   </section>
   <section className="surface findings-surface"><div className="tabs" role="tablist" aria-label="Prescription review sections">
    <button role="tab" aria-selected={tab==='transcription'} className={tab==='transcription'?'active':''} onClick={()=>setTab('transcription')}>Check text</button>
    <button role="tab" aria-selected={tab==='findings'} disabled={!reviewed||editing} className={tab==='findings'?'active':''} onClick={()=>setTab('findings')}>Findings {reviewed&&<span className="tab-count">{issues.length}</span>}</button></div>
    {tab==='transcription'?<div className="tab-body">
      <div className="editor-heading"><h3>Check the prescription text</h3><p>Compare names, doses, instructions and patient details with the image. Correct anything that was read incorrectly.</p></div>
      <label className="form-label" htmlFor="transcription">Prescription text</label>
      <textarea id="transcription" className="transcription-editor" spellCheck={false} value={transcript} onChange={e=>setTranscript(e.target.value)} maxLength={12000} readOnly={reviewed&&!editing}/>
      <div className="editor-footer"><span>{transcript.length} / 12,000 characters</span></div>
      {reviewed&&!editing&&<Notice type="info">Text saved. Choose “Edit text” to correct it again.</Notice>}
      {error&&<Notice type="error">{error}</Notice>}
      {reviewed&&!editing&&<button className="button button-ghost button-full" onClick={()=>{setEditing(true);setTab('transcription')}}>Edit text</button>}
      {(!reviewed||editing)&&<button className="button button-primary button-full" onClick={verify} disabled={busy||!transcript.trim()}>
       {busy?<LoaderCircle className="spin" size={18}/>:<ClipboardCheck size={18}/>} {editing?'Save changes and update findings':'Save text and see findings'}</button>}
    </div>:<div className="tab-body">
      <Notice type="warning">These findings do not confirm that a prescription is safe. A qualified healthcare professional must review it.</Notice>
      {report.reviewed_rule_registry_status==='INVALID_OR_UNAVAILABLE'&&<Notice type="error">Medication reference rules could not be validated. Dose and age checks are unavailable until the local rule file is corrected.</Notice>}
      {report.reviewed_rule_registry_status==='NO_APPROVED_RULES'&&<Notice type="info">Medicine-specific dose and age checks are not available yet. You can still review and correct the prescription text.</Notice>}
      <div className="findings-summary"><div className="finding-number">{issues.length}</div><div><strong>Items to review</strong><p>{medications.length} medication {medications.length===1?'entry':'entries'} found.</p></div></div>
      <FindingsCenter issues={issues} onEdit={()=>{setEditing(true);setTab('transcription')}}/>
      <div className="medication-section"><h3>Prescription details</h3>
        {medications.map((med,i)=>{const f=med.extraction?.fields||{},name=f.medicine||'Unidentified medicine';
         return <div className="medication-card" key={i}><div className="medication-top"><div><span className="med-number">MEDICATION {i+1}</span><h4>{name}</h4></div></div>
         <div className="field-summary">{[['Administered dose',f.dose],['Strength',f.strength],['Frequency',f.frequency],['Age',f.age],['Weight',f.weight],['Route',f.route],['Product identifier',f.product_identifier],['Indication',f.indication],['Population',f.population]].map(([label,value])=><div key={label}><small>{label}</small><strong>{value||'Not captured — check source'}</strong></div>)}</div>
         {med.extraction?.candidate_only&&<p className="medication-uncertainty">Check this medicine name and dose against the image.</p>}
         <div className="rule-summary"><div><small>Dose check</small><strong>{doseLabel(med.reviewed_dose_rule?.status)}</strong></div>
          <div><small>Age check</small><strong>{ageLabel(med.reviewed_age_rule?.status)}</strong></div></div>
         {med.reviewed_dose_rule?.comparison_outcomes?.length>0&&<div className="source-section"><strong>What was compared</strong><ul>{med.reviewed_dose_rule.comparison_outcomes.map(code=><li key={code}>{comparisonLabel(code)}</li>)}</ul></div>}
         {med.reviewed_age_rule?.min_age_years!=null&&<p className="medication-uncertainty">Reviewed age range: {med.reviewed_age_rule.min_age_years}–{med.reviewed_age_rule.max_age_years} years.</p>}
         {med.reviewed_dose_rule?.status!=='NOT_EVALUATED'&&med.reviewed_dose_rule?.status&&<details className="source-section"><summary>How the dose was checked</summary><p>Single amount: {med.reviewed_dose_rule.administered_single} {med.reviewed_dose_rule.dose_unit}; reviewed limit: {med.reviewed_dose_rule.reviewed_max_single} {med.reviewed_dose_rule.dose_unit}. Daily total: {med.reviewed_dose_rule.administered_daily} {med.reviewed_dose_rule.dose_unit}; reviewed limit: {med.reviewed_dose_rule.reviewed_max_daily} {med.reviewed_dose_rule.dose_unit}.</p><p>Source section: {med.reviewed_dose_rule.source_section||'not recorded'} · Version: {med.reviewed_dose_rule.rule_version||'not recorded'} · Review record: {med.reviewed_dose_rule.rule_identifier||'not recorded'}</p></details>}
         {med.reviewed_dose_rule?.status==='NOT_EVALUATED'&&<p className="medication-uncertainty">Dose could not be checked. {med.reviewed_dose_rule?.reason||'A matching medicine reference is needed.'}</p>}
         {f.medicine&&<button className="text-link" onClick={()=>{setOpenReference(o=>({...o,[name]:!o[name]}));lookup(name)}}><BookOpen size={16}/> {openReference[name]?'Hide':'View'} medicine sources <ChevronDown size={15}/></button>}
         {openReference[name]&&<div className="evidence-box"><strong>Medicine sources</strong><p>These are possible matches. Compare the exact product with the prescription.</p>
          {(references[name]?.dailymed||[]).map((item,i)=><div key={'dm'+i}><p><a target="_blank" rel="noopener noreferrer" href={item.url}>DailyMed: {item.title} ↗</a></p><small>Label version: {item.spl_version||'unknown'} · Published: {item.published_date||'unknown'}</small><button type="button" className="text-link" onClick={()=>viewLabel(item.setid)}>{labels[item.setid]?.status==='UNAVAILABLE'?'Try again':'Read label details'}</button>{labels[item.setid]&&<div className="source-section"><p>Possible product match · Revision: {labels[item.setid].effective_time||'not recorded'}</p>{labels[item.setid].reason&&<p>{labels[item.setid].reason}</p>}{Object.entries(labels[item.setid].sections||{}).map(([heading,section])=><details key={heading}><summary>{heading.replaceAll('_',' ')}</summary><p>{section}</p></details>)}</div>}</div>)}
          {(references[name]?.openfda||[]).map((item,i)=><div className="source-section" key={'fda'+i}><p><a target="_blank" rel="noopener noreferrer" href={item.url}>Open drug label ↗</a></p>{Object.entries(item.label_sections_UNVERIFIED_FOR_PRODUCT||{}).map(([heading,section])=><details key={heading}><summary>{heading.replaceAll('_',' ')}</summary><p>{section}</p></details>)}</div>)}
          {med.reviewed_dose_rule?.source_url&&<p><a target="_blank" rel="noopener noreferrer" href={med.reviewed_dose_rule.source_url}>Open qualified-review source ↗</a></p>}</div>}
        </div>})}
      </div>
    </div>}
   </section>
  </div>
  <details className="surface audit-panel"><summary>Text change history</summary><div className="audit-events">{audit.map(event=><div key={event.event_id} className="audit-event"><span className="audit-dot"/><div><strong>{event.action?.replaceAll('_',' ')}</strong><p>{event.event_time?new Date(event.event_time).toLocaleString('en-GB'):'—'}</p></div></div>)}</div></details>
  <div className="workspace-footer"><div><ShieldAlert size={20}/><p>Ask a qualified healthcare professional to review the prescription before making treatment decisions.</p></div>
   <button className="button button-danger-ghost" onClick={remove} disabled={busy}><Trash2 size={16}/> Delete record</button></div>
 </div>;
}
