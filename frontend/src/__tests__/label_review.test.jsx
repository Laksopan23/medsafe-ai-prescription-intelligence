import React from 'react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import PrescriptionWorkspace from '../features/PrescriptionWorkspace.jsx';

afterEach(()=>{cleanup();vi.unstubAllGlobals()});

describe('reviewed source evidence',()=>{
 it('opens full label evidence without showing it as a clinical approval',async()=>{
  vi.stubGlobal('fetch',vi.fn(async url=>{
   let data={events:[]};
   if(url.includes('/reference/label/'))data={status:'UNVERIFIED_LABEL_EVIDENCE',
     effective_time:'20260101',retrieved_utc:'2026-10-22T00:00:00Z',
     sections:{pediatric_use:'Review age applicability'}};
   else if(url.includes('/reference?'))data={status:'CANDIDATES_FOUND',
     dailymed:[{title:'SYNTHMED label candidate',setid:'aabbccdd-1234',
       url:'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=aabbccdd-1234',
       spl_version:'4',published_date:'Oct 2026'}],openfda:[]};
   return {ok:true,headers:{get:()=> 'application/json'},json:async()=>data};
  }));
  const detail={id:'fake-id',filename:'fictional.png',engine:'tesseract',
   reviewer_confirmed:true,corrected_text:'Medicine: SYNTHMED',ocr:{regions:[]},
   image_url:'/api/prescriptions/fake-id/image',report:{issues:[],medications:[{
    extraction:{fields:{medicine:'SYNTHMED'}},
    reviewed_dose_rule:{status:'NOT_EVALUATED'},
    reviewed_age_rule:{status:'UNABLE_TO_VALIDATE'},
   }]}};
  render(<PrescriptionWorkspace detail={detail} onReviewed={()=>{}} onDeleted={()=>{}}/>);
  fireEvent.click(screen.getByRole('button',{name:/find label evidence/i}));
  fireEvent.click(await screen.findByRole('button',{name:/read source label sections/i}));
  expect(await screen.findByText(/source status: unverified_label_evidence/i)).toBeTruthy();
  expect(screen.getByText(/not been matched to the patient or approved as a dose rule/i)).toBeTruthy();
  expect(screen.getByText(/review age applicability/i)).toBeTruthy();
 });
});
