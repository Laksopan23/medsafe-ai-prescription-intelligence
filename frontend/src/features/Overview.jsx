import React from 'react';
import { Activity, ArrowRight, BrainCircuit, ClipboardCheck, Clock3, FileText, ShieldAlert, UploadCloud } from 'lucide-react';
import {Badge,EmptyState,StatCard} from '../components/Status.jsx';
import { formatDate,formatEngine } from '../lib/api.js';
export default function Overview({stats={},records=[],models={},go,open}){
 const recent=records.slice(0,5);const ready=Object.entries(models.benchmark_engines||{}).filter(([,enabled])=>enabled).length;
 return <div className="stack-lg">
  <section className="hero-panel">
   <div className="hero-content"><div className="hero-tag"><span className="hero-spark"/> PRESCRIPTION REVIEW</div>
    <h2>Upload. Check the text. <em>Review the findings.</em></h2>
    <p>Start with a prescription image, correct anything read incorrectly, and see which details need attention.</p>
    <button className="button button-white" onClick={()=>go('new')}><UploadCloud size={18}/> New prescription <ArrowRight size={17}/></button></div>
   <div className="hero-art" aria-hidden="true"><div className="art-halo halo-one"/><div className="art-halo halo-two"/>
    <div className="art-document"><div className="art-rx">Rx</div><span/><span/><span className="short"/><div className="art-medicine"><Activity size={22}/><div><b>Review details</b><small>Compare with the original</small></div></div></div>
    <div className="art-badge"><ClipboardCheck size={21}/></div></div>
  </section>
  <div className="stat-grid">
   <StatCard icon={FileText} label="Prescriptions" value={stats.total??records.length} hint="Saved on this computer" tone="blue"/>
   <StatCard icon={ClipboardCheck} label="Text checked" value={stats.reviewed??0} hint="Reviewed against the image" tone="teal"/>
   <StatCard icon={Clock3} label="Need text review" value={stats.pending??0} hint="Open to correct the text" tone="amber"/>
   <StatCard icon={BrainCircuit} label="Reading methods ready" value={ready+'/4'} hint="Available options" tone="violet"/>
  </div>
  <div className="overview-grid">
   <section className="surface recent-panel"><div className="section-top"><div><h3>Recent prescriptions</h3><p>Access your most recent review sessions</p></div>
    <button className="text-link" onClick={()=>go('library')}>View all <ArrowRight size={16}/></button></div>
    {recent.length?<div className="table-scroll"><table className="data-table"><thead><tr><th>Prescription</th><th>OCR engine</th><th>Review status</th><th>Created</th><th></th></tr></thead>
    <tbody>{recent.map(row=><tr key={row.id}><td><div className="file-cell"><span className="file-icon"><FileText size={17}/></span><span>{row.filename||'Prescription'}</span></div></td>
      <td>{formatEngine(row.engine)}</td><td><Badge tone={row.reviewer_confirmed?'teal':'amber'}>{row.reviewer_confirmed?'Text reviewed':'Review required'}</Badge></td>
      <td>{formatDate(row.created)}</td><td><button className="table-action" onClick={()=>open(row.id)}>Open <ArrowRight size={14}/></button></td></tr>)}</tbody></table></div>:
    <EmptyState icon={FileText} title="No prescriptions yet" description="Upload your first prescription to start a review session." action={<button className="button button-primary" onClick={()=>go('new')}>New analysis</button>}/>}
   </section>
   <aside className="surface assurance-panel"><div className="section-top"><div><h3>Three simple steps</h3></div></div>
    <div className="assurance-item"><span className="assurance-dot"/><div><strong>1. Upload</strong><p>Choose a clear prescription image.</p></div></div>
    <div className="assurance-item"><span className="assurance-dot"/><div><strong>2. Check</strong><p>Compare the text with the original and correct errors.</p></div></div>
    <div className="assurance-item"><span className="assurance-dot"/><div><strong>3. Review</strong><p>See the findings and anything the app could not check.</p></div></div>
   </aside>
  </div>
 </div>;
}
