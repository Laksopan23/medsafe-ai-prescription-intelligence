import React,{useRef,useState} from 'react';
import { ArrowRight, CloudUpload, FileImage, Info, LoaderCircle, ShieldCheck, X } from 'lucide-react';
import {Notice} from '../components/Status.jsx';
import OCRComparison from './OCRComparison.jsx';
import {uploadPrescription,formatEngine} from '../lib/api.js';
const TYPES=/\.(png|jpe?g|webp|pdf)$/i;
export default function Upload({models={},onUploaded}){
 const ref=useRef(null);const [file,setFile]=useState(null),[engine,setEngine]=useState('tesseract');
 const [preprocess,setPreprocess]=useState('none'),[analysisMode,setAnalysisMode]=useState('single');
 const [drag,setDrag]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const select=(f)=>{if(!f)return;if(!TYPES.test(f.name)){setError('Choose a PNG, JPG, WEBP, or single-page PDF.');return}if(f.size>12*1024*1024){setError('Maximum file size is 12 MB.');return}setFile(f);setError('')};
 const submit=async()=>{if(!file)return;setBusy(true);setError('');try{const result=await uploadPrescription(file,engine,preprocess);await onUploaded(result.id)}catch(e){setError(e.message)}finally{setBusy(false)}};
 const engines=[['tesseract','Tesseract','Local baseline OCR'],['easyocr','EasyOCR','Research comparison'],['paddleocr','PaddleOCR','Research comparison'],['craft_trocr','CRAFT + TrOCR','Research model comparison']];
 return <><div className="upload-layout"><section className="surface upload-card">
  <div className="section-top"><div><h3>Choose a prescription</h3><p>Upload a clear image or a one-page PDF. You can check the text next.</p></div><div className="step-label">STEP 1 OF 3</div></div>
  <input ref={ref} type="file" accept=".png,.jpg,.jpeg,.webp,.pdf" hidden onChange={e=>select(e.target.files?.[0])}/>
  <div role="button" tabIndex={0} aria-label="Choose a prescription file" onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();ref.current?.click()}}}
   onClick={()=>ref.current?.click()} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)}
   onDrop={e=>{e.preventDefault();setDrag(false);select(e.dataTransfer.files?.[0])}}
   className={'drop-area'+(drag?' dragging':'')}><div className="drop-icon"><CloudUpload size={33}/></div>
   <h3>Drag and drop your prescription</h3><p>or <span>browse files</span> from your computer</p><small>PNG, JPG, WEBP or PDF · Maximum 12 MB</small></div>
  {file&&<div className="selected-file"><FileImage size={20}/><div><strong>{file.name}</strong><small>{(file.size/1024/1024).toFixed(2)} MB · Ready to analyze</small></div><button className="icon-button" aria-label="Remove file" onClick={()=>setFile(null)}><X size={18}/></button></div>}
  <div className="form-label">What would you like to do?</div>
  <div className="analysis-mode-switch" role="group" aria-label="Analysis mode">
   <button type="button" className={analysisMode==='single'?'active':''} aria-pressed={analysisMode==='single'} onClick={()=>setAnalysisMode('single')}>Review a prescription <small>Read, correct and save its details</small></button>
   <button type="button" className={analysisMode==='compare'?'active':''} aria-pressed={analysisMode==='compare'} onClick={()=>setAnalysisMode('compare')}>Compare text readers <small>See how four methods read the image</small></button>
  </div>
  <details className="upload-advanced"><summary>Advanced options</summary>
  {analysisMode==='single'&&<><div className="form-label">Text-reading method</div><div className="engine-grid">{engines.map(([id,label,description])=><button key={id} type="button" onClick={()=>setEngine(id)}
   className={'engine-option'+(engine===id?' active':'')}><div className="radio-indicator"/><strong>{label}</strong><span>{description}</span>{models.benchmark_engines?.[id==='craft_trocr'?'trocr':id]===false&&<small>Requires local model setup</small>}</button>)}</div></>}
  <label className="form-label" htmlFor="preprocessing-mode">Image adjustment</label>
  <div className="preprocessing-control">
    <select id="preprocessing-mode" value={preprocess} onChange={e=>setPreprocess(e.target.value)}>
      <option value="none">Original image — no changes (fair baseline)</option>
      <option value="clahe">Contrast enhancement + denoising (CLAHE)</option>
      <option value="adaptive">Adaptive black-and-white threshold</option>
      <option value="deskew_clahe">Automatic deskew + contrast enhancement</option>
    </select>
    <p>Your original document remains unchanged.</p>
  </div>
  </details>
  {error&&<Notice type="error">{error}</Notice>}
  {analysisMode==='single'&&<button className="button button-primary submit-upload" disabled={!file||busy} onClick={submit}>{busy?<><LoaderCircle size={19} className="spin"/> Reading image…</>:<>Read prescription <ArrowRight size={19}/></>}</button>}
  {analysisMode==='compare'&&<div className="upload-mode-note"><Info size={17}/><span>Compare all four engines without saving a prescription. Install optional models to enable all results. The comparison accepts files up to 8 MB.</span></div>}
 </section>
 <aside className="upload-aside"><div className="surface"><div className="aside-illustration"><ShieldCheck size={27}/></div><h3>How it works</h3>
  <ol className="process-steps"><li><span>01</span><div><strong>Upload</strong><p>Choose the prescription image.</p></div></li>
   <li><span>02</span><div><strong>Check the text</strong><p>Correct names, amounts and instructions against the image.</p></div></li>
   <li><span>03</span><div><strong>Review findings</strong><p>See what could and could not be checked.</p></div></li></ol></div>
 </aside></div>{analysisMode==='compare'&&<div className="upload-comparison"><OCRComparison initialFile={file} initialMode={preprocess} embedded/></div>}</>;
}
