import React from 'react';
import {afterEach,describe,expect,it} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import Research from '../features/Research.jsx';

afterEach(()=>cleanup());

describe('model comparison page',()=>{
  it('shows availability and keeps optional measurements separate',()=>{
    render(<Research models={{benchmark_engines:{tesseract:true,easyocr:false}}}
      benchmarks={{status:'NO_INDEPENDENT_RESULTS',engines:{}}}
      historical={{n_aligned_images:0,engines:{}}}/>);
    expect(screen.getByText('Compare text-reading methods')).toBeTruthy();
    expect(screen.getByText('Standard text reader')).toBeTruthy();
    expect(screen.getAllByText('Setup needed').length).toBeGreaterThan(0);
    fireEvent.click(screen.getByText(/current test results/i));
    expect(screen.getByText(/no independently checked test results have been loaded/i)).toBeTruthy();
    expect(screen.queryByText(/earlier experiment results/i)).toBeNull();
  });

  it('labels development numbers as development numbers',()=>{
    render(<Research benchmarks={{status:'DEVELOPMENT_ONLY',engines:{
      tesseract:{n_succeeded:1,n_total:1,metrics:{ocr:{CER:.12}}}
    }}} historical={{engines:{}}}/>);
    fireEvent.click(screen.getByText(/current test results/i));
    expect(screen.getByText(/development measurements, not an independent accuracy result/i)).toBeTruthy();
    expect(screen.getByText('12.00%')).toBeTruthy();
  });
});
