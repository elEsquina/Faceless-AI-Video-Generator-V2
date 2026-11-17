/** Original deterministic utilities; installed Three/Fiber/Remotion/GSAP only. */
import React,{useLayoutEffect,useMemo} from 'react';
import * as THREE from 'three';
import {useThree} from '@react-three/fiber';
import {ThreeCanvas} from '@remotion/three';
import {AbsoluteFill,useCurrentFrame,useVideoConfig,delayRender,continueRender} from 'remotion';
import {gsap} from 'gsap';
export type V3=[number,number,number];
export const smooth=(u:number)=>{const t=Math.max(0,Math.min(1,u));return t*t*(3-2*t);};
export const palette={ink:'#ebf5ff',teal:'#50dfd0',gold:'#ffd06e',navy:'#0b1830'};
export function World({children,background='#0b1830'}:{children:React.ReactNode;background?:string}) {
 const {width,height}=useVideoConfig();
 return <ThreeCanvas width={width} height={height} shadows gl={{antialias:true,toneMapping:THREE.ACESFilmicToneMapping}}
  camera={{position:[5,4,8],fov:38,near:.1,far:100}}>
  <color attach="background" args={[background]}/><fog attach="fog" args={[background,18,45]}/><Lights/>{children}</ThreeCanvas>;
}
export function Lights({warm=false}:{warm?:boolean}) {
 return <><hemisphereLight args={['#c5e8ff','#19243e',1.5]}/>
  <directionalLight position={[4,8,5]} intensity={3.2} color={warm?'#ffcc8b':'#fff0d8'} castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024}/>
  <directionalLight position={[-5,2,-3]} intensity={2} color="#4b9fff"/>
  <pointLight position={[0,3,-5]} intensity={35} color="#49dccc"/></>;
}
export function Camera({from,to,target,progress=0,fov=38}:{from:V3;to:V3;target:V3;progress?:number;fov?:number}) {
 const {camera}=useThree();
 useLayoutEffect(()=>{camera.position.lerpVectors(new THREE.Vector3(...from),new THREE.Vector3(...to),smooth(progress));
  camera.lookAt(...target);const c=camera as THREE.PerspectiveCamera;c.fov=fov;c.updateProjectionMatrix();
 },[camera,...from,...to,...target,progress,fov]);return null;
}
/** Fresh state and paused timeline make arbitrary frame order safe. */
export function timelineAt<T extends object>(factory:()=>T,build:(tl:gsap.core.Timeline,state:T)=>void,seconds:number):T {
 const state=factory();const tl=gsap.timeline({paused:true});build(tl,state);
 tl.seek(Math.max(0,seconds),false);tl.kill();return state;
}
export function Outline({geometry,color='#071222'}:{geometry:THREE.BufferGeometry;color?:string}) {
 const edges=useMemo(()=>new THREE.EdgesGeometry(geometry,28),[geometry]);
 useLayoutEffect(()=>()=>edges.dispose(),[edges]);
 return <lineSegments geometry={edges}><lineBasicMaterial color={color} transparent opacity={.6}/></lineSegments>;
}
export const physical=(color:string,metalness=.15,roughness=.35)=>new THREE.MeshStandardMaterial({color,metalness,roughness});
export function Flow({path,count=12,time=0,color='#ffcf70',speed=.25}:{path:THREE.Curve<THREE.Vector3>;count?:number;time?:number;color?:string;speed?:number}) {
 return <>{Array.from({length:count},(_,i)=>{const u=((i/count+time*speed)%1+1)%1;return <mesh key={i} position={path.getPointAt(u)}>
  <sphereGeometry args={[.065,12,8]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.6}/></mesh>;})}</>;
}
export function Label({x,y,children,color=palette.ink}:{x:number;y:number;children:React.ReactNode;color?:string}) {
 return <div data-qa={String(children)} style={{position:'absolute',left:`${x*100}%`,top:`${y*100}%`,fontFamily:'Arial',fontSize:26,color,
  background:'#0b1830de',borderLeft:`3px solid ${palette.teal}`,padding:'9px 14px',borderRadius:5}}>{children}</div>;
}
export function Chapter({number,title,subtitle}:{number:string;title:string;subtitle:string}) {
 return <div style={{position:'absolute',top:32,left:48,color:palette.ink,fontFamily:'Arial'}}>
  <div style={{color:palette.teal,fontSize:18,letterSpacing:4}}>{number} / ENERGY IN MOTION</div>
  <div data-qa="chapter-title" style={{fontSize:42,fontWeight:700,marginTop:10}}>{title}</div>
  <div data-qa="chapter-subtitle" style={{fontSize:23,color:'#a8c3dc',marginTop:8}}>{subtitle}</div></div>;
}
export function Dissolve({children,durationInFrames}:{children:React.ReactNode;durationInFrames:number}) {
 const f=useCurrentFrame(),a=Math.min(1,(f+1)/8,(durationInFrames-f)/8);
 return <AbsoluteFill style={{opacity:Math.max(0,a)}}>{children}</AbsoluteFill>;
}
export function circuitMaterial() {
 return new THREE.ShaderMaterial({uniforms:{base:{value:new THREE.Color('#154e7a')}},
 vertexShader:'varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
 fragmentShader:`varying vec2 vUv; uniform vec3 base; void main(){vec2 g=abs(fract(vUv*vec2(6.,10.))-.5);
 float line=step(.465,max(g.x,g.y));gl_FragColor=vec4(mix(base,vec3(.35,.8,.95),line*.6),1.);}`});
}
/** Preview-only evidence. Rectangles come from rendered DOM, not authored guesses. */
export function LayoutProbe({enabled=false}:{enabled?:boolean}) {
 const frame=useCurrentFrame();
 const handle=useMemo(()=>enabled?delayRender('Measured DOM layout'):null,[enabled,frame]);
 useLayoutEffect(()=>{
  if(!enabled||handle===null)return;
  let raf=0,done=false,tries=0;
  const measure=()=>{
   const root=document.querySelector('[data-qa-root]');const viewport=root?.getBoundingClientRect();
   if(!root||!viewport||viewport.width<=0){if(tries++>120)throw new Error('DOM layout was not measurable');raf=requestAnimationFrame(measure);return;}
   const objects=Array.from(root.querySelectorAll('[data-qa]')).map(node=>{
    const b=node.getBoundingClientRect();return {id:node.getAttribute('data-qa'),kind:'text',
     bounds:[(b.left-viewport.left)/viewport.width,(b.top-viewport.top)/viewport.height,(b.right-viewport.left)/viewport.width,(b.bottom-viewport.top)/viewport.height],
     font_px:parseFloat(getComputedStyle(node).fontSize),collision_group:'labels'};
   });
   console.log('LAYOUT_EVIDENCE '+JSON.stringify({frame,objects}));done=true;continueRender(handle);
  };
  raf=requestAnimationFrame(measure);
  return ()=>{cancelAnimationFrame(raf);if(!done)continueRender(handle);};
 },[enabled,frame,handle]);return null;
}
export function projectedBounds(object:THREE.Object3D,camera:THREE.Camera):number[] {
 object.updateWorldMatrix(true,true);camera.updateMatrixWorld();const points:THREE.Vector3[]=[];
 object.traverse(child=>{
  const mesh=child as THREE.Mesh;const positions=mesh.geometry?.attributes?.position;if(!positions)return;
  for(let i=0;i<positions.count;i++)points.push(new THREE.Vector3().fromBufferAttribute(positions as THREE.BufferAttribute,i).applyMatrix4(child.matrixWorld).project(camera));
 });
 return [Math.min(...points.map(p=>p.x))*.5+.5,.5-Math.max(...points.map(p=>p.y))*.5,Math.max(...points.map(p=>p.x))*.5+.5,.5-Math.min(...points.map(p=>p.y))*.5];
}
export function ProjectionProbe({enabled=false}:{enabled?:boolean}) {
 const frame=useCurrentFrame(),{scene,camera}=useThree();
 useLayoutEffect(()=>{
  if(!enabled)return;const objects:any[]=[];
  scene.traverse(obj=>{if(obj.name.startsWith('qa_subject'))objects.push({id:obj.name,kind:'diagram',role:'subject',bounds:projectedBounds(obj,camera),min_area:.003});});
  console.log('PROJECTION_EVIDENCE '+JSON.stringify({frame,objects}));
 },[frame,enabled,scene,camera]);return null;
}

export function Crossfade({progress,previous,children}:{progress:number;previous?:React.ReactNode;children:React.ReactNode}) {
 const alpha=smooth(progress);
 return <>{previous&&alpha<1&&<AbsoluteFill style={{opacity:1-alpha}}>{previous}</AbsoluteFill>}
  <AbsoluteFill style={{opacity:alpha}}>{children}</AbsoluteFill></>;
}
