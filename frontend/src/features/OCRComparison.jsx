import React,{useEffect,useRef,useState} from 'react';
import {ArrowRight,ClipboardCopy,FileImage,LoaderCircle,ShieldAlert,UploadCloud,XCircle} from 'lucide-react';
import {Badge,Notice} from '../components/Status.jsx';
import {formatEngine,request,saveJSON} from '../lib/api.js';

const ENGINES=['tesseract','easyocr','paddleocr','craft_trocr'];
const MODES=[['none','Original image'],['clahe','Contrast enhancement'],['adaptive','Adaptive black and white'],['deskew_clahe','Deskew + contrast']];
const FIELDS=[['medicine','Medicine'],['dose','Administered dose'],['frequency','Frequency'],['age','Patient age'],['route','Route'],['strength','Product strength']];
const pct=value=>Number.isFinite(value)?(value*100).toFixed(2)+'%':'—';
const SECONDS=value=>Number.isFinite(value)?value.toFixed(3)+' s':'—';
const statusLabel=value=>value==='COMPLETED'?'Processed':'Unavailable';

export default function OCRComparison({initialFile=null,initialMode='none',embedded=false}){
 const picker=useRef(null);
 const [file,setFile]=useState(initialFile),[mode,setMode]=useState(initialMode);
 const [reference,setReference]=useState(''),[referenceOpen,setReferenceOpen]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState(null);
 const [active,setActive]=useState('tesseract'),[preview,setPreview]=useState('');
 useEffect(()=>{if(embedded){setFile(initialFile);setResult(null);setError('')}},[embedded,initialFile]);
 useEffect(()=>{setMode(initialMode);if(embedded)setResult(null)},[initialMode,embedded]);
 useEffect(()=>{if(!file||file.type==='application/pdf'){setPreview('');return}
  const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url);
 },[file]);
 const choose=(selected)=>{
  setResult(null);setError('');
  if(!selected)return;
  if(!/\.(png|jpe?g|webp|pdf)$/i.test(selected.name)){setError('Choose a PNG, JPG, WEBP or single-page PDF.');return}
  if(selected.size>8*1024*1024){setError('Comparison file limit is 8 MB.');return}
  setFile(selected);
 };
 const compare=async()=>{
  if(!file)return;
  setBusy(true);setError('');setResult(null);
  try{
   const payload=new FormData();payload.append('file',file);
   if(reference.trim())payload.append('reference_text',reference);
   const data=await request('/compare?preprocess='+encodeURIComponent(mode),{method:'POST',body:payload});
   setResult(data);
   setActive(ENGINES.find(name=>data.engines?.[name]?.status==='COMPLETED')||ENGINES[0]);
  }catch(exc){setError(exc.message)}finally{setBusy(false)}
 };
 const completed=ENGINES.filter(engine=>result?.engines?.[engine]?.status==='COMPLETED');
 const ranked=completed.filter(engine=>result?.engines?.[engine]?.reference_metrics?.cer!=null)
  .sort((a,b)=>result.engines[a].reference_metrics.cer-result.engines[b].reference_metrics.cer);
 const top=ranked[0];
 const selected=result?.engines?.[active]||{};
 const extracted=selected.extraction||{};
 return <section className={'surface comparison-panel'+(embedded?' comparison-embedded':'')}>
  <div className="section-top"><div><h3>Try the same image with each method</h3>
   <p>One prescription, the same preprocessing, four independent recognizers. Choose a method below to read its text.</p></div></div>
  <div className="comparison-form">
   {!embedded&&<div className="comparison-source">
    <input ref={picker} type="file" accept=".png,.jpg,.jpeg,.webp,.pdf" hidden onChange={e=>choose(e.target.files?.[0])}/>
    <button type="button" className="comparison-picker" onClick={()=>picker.current?.click()}>
     <div className="comparison-picker-icon">{preview?<img src={preview} alt="Prescription preview"/>:<UploadCloud size={24}/>}</div>
     <span><strong>{file?file.name:'Choose a prescription for comparison'}</strong><small>Up to 8 MB · Source not stored by comparison endpoint</small></span>
     <FileImage size={19}/></button>
   </div>}
   {embedded&&<div className="comparison-selected-file">
    <FileImage size={20}/><div><strong>{file?.name||'No prescription selected yet'}</strong>
    <small>{file?'Use the uploaded image above. This comparison does not create a prescription record.':'Choose an image above to compare the engines.'}</small></div></div>}
   {!embedded&&<label className="comparison-mode" htmlFor="comparison-mode">Image preprocessing
    <select id="comparison-mode" value={mode} onChange={e=>{setMode(e.target.value);setResult(null)}}>
     {MODES.map(([id,label])=><option key={id} value={id}>{label}</option>)}
    </select></label>}
   <button type="button" className="button button-primary comparison-submit" onClick={compare} disabled={!file||busy||file.size>8*1024*1024}>
    {busy?<LoaderCircle className="spin" size={17}/>:<ArrowRight size={17}/>}
    {busy?'Running all available engines…':'Run four-model comparison'}</button>
  </div>
  <details className="comparison-reference" open={referenceOpen} onToggle={e=>setReferenceOpen(e.currentTarget.open)}>
   <summary>Optional: compare against a manually checked reference transcript</summary>
   <div><label htmlFor={'comparison-reference-text'+(embedded?'-upload':'')}>Reference text (for this image only)</label>
    <textarea id={'comparison-reference-text'+(embedded?'-upload':'')} rows={4} maxLength={12000}
     placeholder="Type exactly what you verified from the source image. This is not independent thesis ground truth."
     value={reference} onChange={e=>{setReference(e.target.value);setResult(null)}}/>
    <p>Character error rate (CER) and word error rate (WER) appear only when you provide this reference. This is one user-checked example, not a clinical or thesis accuracy result. Re-run to apply changes.</p>
   </div>
  </details>
  {file?.size>8*1024*1024&&<div className="comparison-notice"><Notice type="warning">Comparison accepts files up to 8 MB; choose a smaller source image.</Notice></div>}
  {error&&<div className="comparison-notice"><Notice type="error">{error}</Notice></div>}
  {result&&<div className="comparison-result" aria-live="polite">
   <div className="comparison-result-header"><div><h4>Results on this prescription</h4>
    <p>{result.completed_engines} of {result.n_engines} methods completed. Select a method to compare its text with the image.</p></div>
    <button type="button" className="button button-ghost" onClick={()=>saveJSON('medsafe-ocr-comparison.json',result)}>Download results</button></div>
   <details className="comparison-stats"><summary>View scores and timing</summary>
   <div className="comparison-tablescroll"><table className="comparison-table"><caption>Current image: method output comparison. Detected fields are not an accuracy score.</caption>
    <thead><tr><th scope="col">OCR engine</th><th scope="col">Inference time</th><th scope="col">Text regions</th><th scope="col">Fields detected</th><th scope="col">CER</th><th scope="col">WER</th><th scope="col">Availability</th></tr></thead>
    <tbody>{ENGINES.map(engine=>{const r=result.engines?.[engine]||{},ok=r.status==='COMPLETED';
     return <tr key={engine} className={engine===active?'comparison-selected-row':''}>
      <td><button type="button" className="comparison-model-link" onClick={()=>setActive(engine)} aria-pressed={active===engine}>{formatEngine(engine)}</button></td>
      <td>{ok?SECONDS(r.elapsed_seconds):'—'}</td><td>{ok?r.region_count??0:'—'}</td>
      <td>{ok?(r.extraction?.field_coverage?.detected??0)+' / '+(r.extraction?.field_coverage?.possible??0):'—'}</td>
      <td>{ok?pct(r.reference_metrics?.cer):'—'} {top===engine&&<span className="comparison-lowest">Lowest on entered text</span>}</td>
      <td>{ok?pct(r.reference_metrics?.wer):'—'}</td><td><Badge tone={ok?'teal':'amber'}>{statusLabel(r.status)}</Badge></td></tr>})}</tbody></table></div>
   <p className="comparison-metric-note">{result.reference_used?'Text error rates compare against the text you entered for this image.':'No verified transcription provided: text accuracy cannot be measured for this image.'} Time shown is for each reading method.</p>
   </details>
   <div className="comparison-switcher" role="group" aria-label="Inspect OCR engine results">
    {ENGINES.map(engine=><button type="button" key={engine} className={engine===active?'is-active':''} aria-pressed={active===engine} onClick={()=>setActive(engine)}>{formatEngine(engine)}</button>)}
   </div>
   <div className="comparison-inspector">
    <div className="comparison-inspector-heading"><h4>{formatEngine(active)} — detailed output</h4><Badge tone={selected.status==='COMPLETED'?'teal':'amber'}>{statusLabel(selected.status)}</Badge></div>
    {selected.status==='COMPLETED'?<>
     <div className="comparison-inspector-columns">
      <div><div className="comparison-panel-label">Text read from image</div>
       <pre className="comparison-raw-text">{selected.text||'No readable text returned by this engine.'}</pre>
       <button className="text-link" type="button" onClick={()=>navigator.clipboard?.writeText(selected.text||'')}><ClipboardCopy size={15}/> Copy text</button>
      </div>
      <div><div className="comparison-panel-label">Possible prescription details</div>
       {(extracted.medications||[]).map(med=><div key={med.index} className="comparison-extraction-block">
        <strong>Medication {med.index}{med.candidate_only?' · Check against image':''}</strong>
        <dl>{FIELDS.map(([key,label])=><div key={key}><dt>{label}</dt><dd>{med.fields?.[key]||'Not recognized'}</dd></div>)}</dl>
        {med.source_line&&<p className="comparison-source-line">OCR source line: {med.source_line}</p>}
       </div>)}
      </div>
     </div>
     {selected.warnings?.length>0&&<details className="comparison-warnings"><summary>{selected.warnings.length} OCR diagnostic note(s)</summary>
      <ul>{selected.warnings.map((w,i)=><li key={i}>{w.replaceAll('_',' ')}</li>)}</ul></details>}
    </>:<div className="comparison-unavailable"><XCircle size={19}/><p>{selected.reason||'The model is not ready in this environment. Install its dependencies and weights to compare it.'}</p></div>}
   </div>
   <div className="comparison-disclaimer"><ShieldAlert size={19}/><div>Compare every result with the original image before using the text.</div></div>
  </div>}
 </section>;
}
