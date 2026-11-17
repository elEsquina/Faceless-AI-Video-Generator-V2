/** Run inside the existing Remotion container; reuse browser and collect real logs. */
const fs=require('fs'),path=require('path'),{createRequire}=require('module');
const appRequire=createRequire('/app/package.json');
const {bundle}=appRequire('@remotion/bundler');
const {openBrowser,selectComposition,renderStill}=appRequire('@remotion/renderer');
(async()=>{
 const job=process.argv[2],frames=process.argv[3].split(',').map(Number),out=path.join(job,'qa','preview');
 const inputProps={collectLayout:true};const samples=new Map();
 const capture=log=>{
  const match=log.text.match(/(?:LAYOUT|PROJECTION)_EVIDENCE (\{.*\})/);if(!match)return;
  const event=JSON.parse(match[1]);const objects=samples.get(event.frame)||new Map();
  for(const object of event.objects)objects.set(object.id,object);samples.set(event.frame,objects);
 };
 const serveUrl=await bundle({entryPoint:'/app/src/index.tsx',outDir:path.join(job,'qa','preview_bundle')});
 const browser=await openBrowser('chrome',{browserExecutable:'/usr/bin/chromium',chromiumOptions:{gl:'swangle',flags:{'enable-unsafe-swiftshader':true}}});
 try {
  const composition=await selectComposition({serveUrl,id:'MainScene',inputProps,puppeteerInstance:browser,onBrowserLog:capture});
  for(const frame of frames){
   await renderStill({serveUrl,composition,inputProps,puppeteerInstance:browser,frame,scale:.5,
    output:path.join(out,`frame_${String(frame).padStart(4,'0')}.png`),onBrowserLog:capture});
   console.log('PREVIEW_FRAME_DONE',frame);
  }
 }finally{await browser.close({silent:true});}
 const evidence=Array.from(samples.entries()).filter(([frame])=>frames.includes(frame)).map(([frame,objects])=>({time:frame/30,objects:Array.from(objects.values())}));
 if(evidence.length)fs.writeFileSync(path.join(job,'qa','layout_scene_001.json'),JSON.stringify({samples:evidence},null,2));
 console.log('GEOMETRY_SAMPLES',evidence.length);
})().catch(error=>{console.error(error);process.exit(1);});
