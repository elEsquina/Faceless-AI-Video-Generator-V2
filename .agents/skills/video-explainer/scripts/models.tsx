/** Original configurable science objects; dimensions in world units. */
import React,{useMemo} from 'react';
import * as THREE from 'three';
import {Flow,circuitMaterial,Outline} from './cinematic';

export function PanelAssembly({rotation=[-.15,-.2,0],position=[0,0,0]}:{rotation?:[number,number,number];position?:[number,number,number]}) {
 const geometry=useMemo(()=>new THREE.BoxGeometry(3.7,2.35,.16),[]);
 const cell=useMemo(circuitMaterial,[]);
 return <group name="qa_subject_panel" rotation={rotation} position={position}>
  <mesh geometry={geometry} castShadow><meshStandardMaterial color="#9eb1c6" metalness={.8} roughness={.25}/><Outline geometry={geometry}/></mesh>
  <mesh position={[0,0,.095]} material={cell}><planeGeometry args={[3.48,2.13]}/></mesh>
  {Array.from({length:5},(_,i)=><mesh key={i} position={[-1.4+i*.70,0,.11]}><boxGeometry args={[.016,2.12,.012]}/><meshStandardMaterial color="#c1d6e3" metalness={.7}/></mesh>)}
  {[-1.3,1.3].map(x=><mesh key={x} position={[x,-1.6,-.12]} rotation={[0,0,-.1]} castShadow><boxGeometry args={[.12,1,.12]}/><meshStandardMaterial color="#65788e" metalness={.7}/></mesh>)}
 </group>;
}
export function CellLayers({spread=0,time=0}:{spread?:number;time?:number}) {
 return <group name="qa_subject_cell" rotation={[-.20,-.4,0]}>
  {[
    {z:.34+spread*.8,c:'#88d5ee',w:3.6,h:2.15,alpha:.2},
    {z:.12+spread*.25,c:'#267ca8',w:3.45,h:2.05,alpha:1},
    {z:-.12-spread*.25,c:'#173e73',w:3.45,h:2.05,alpha:1},
    {z:-.34-spread*.8,c:'#b2c3cf',w:3.6,h:2.15,alpha:1}
   ].map((l,i)=><mesh key={i} position={[0,0,l.z]} castShadow>
    <boxGeometry args={[l.w,l.h,.10]}/><meshStandardMaterial color={l.c} transparent={l.alpha<1} opacity={l.alpha} roughness={.3} metalness={i===3?.7:.15} depthWrite={l.alpha===1}/></mesh>)}
  {Array.from({length:14},(_,i)=><mesh key={i} position={[-1.4+(i%7)*.46,-.7+Math.floor(i/7)*1.4,.24+spread*.4]}>
   <sphereGeometry args={[.045,12,8]}/><meshStandardMaterial color="#ffd474" emissive="#f4bd54" emissiveIntensity={1}/></mesh>)}
 </group>;
}
export function Wire({points,time=0,color='#54dfd0',particles=true}:{points:[number,number,number][];time?:number;color?:string;particles?:boolean}) {
 const path=useMemo(()=>new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),[JSON.stringify(points)]);
 const geometry=useMemo(()=>new THREE.TubeGeometry(path,80,.028,8,false),[path]);
 return <><mesh geometry={geometry}><meshStandardMaterial color={color} emissive={color} emissiveIntensity={.3}/></mesh>
  {particles&&<Flow path={path} count={18} time={time} speed={.17}/>}</>;
}
export function Converter({position=[0,0,0]}:{position?:[number,number,number]}) {
 return <group name="qa_subject_converter" position={position}>
  <mesh castShadow><boxGeometry args={[1.2,1.6,.55]}/><meshStandardMaterial color="#c8d8e4" metalness={.55} roughness={.3}/></mesh>
  <mesh position={[0,.27,.29]}><boxGeometry args={[.83,.54,.025]}/><meshStandardMaterial color="#17324e"/></mesh>
  <mesh position={[0,-.17,.31]}><sphereGeometry args={[.055,16,8]}/><meshStandardMaterial color="#60f8b2" emissive="#60f8b2" emissiveIntensity={1.5}/></mesh>
  {Array.from({length:5},(_,i)=><mesh key={i} position={[-.4+i*.2,-.57,.29]}><boxGeometry args={[.06,.25,.03]}/><meshStandardMaterial color="#3a5368"/></mesh>)}
 </group>;
}
export function Home({position=[0,0,0],lit=false}:{position?:[number,number,number];lit?:boolean}) {
 const roof=useMemo(()=>{
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute([-1,.65,.8,1,.65,.8,0,1.5,.8,-1,.65,-.8,1,.65,-.8,0,1.5,-.8],3));
  g.setIndex([0,1,2,3,5,4,0,2,5,0,5,3,2,1,4,2,4,5,0,3,4,0,4,1]);g.computeVertexNormals();return g;
 },[]);
 return <group name="qa_subject_home" position={position}>
  <mesh castShadow><boxGeometry args={[1.8,1.5,1.3]}/><meshStandardMaterial color="#b4cdc9" roughness={.8}/></mesh>
  <mesh geometry={roof} castShadow><meshStandardMaterial color="#cd8061"/></mesh>
  {[-.48,.48].map(x=><mesh key={x} position={[x,.15,.67]}><boxGeometry args={[.38,.42,.05]}/>
   <meshStandardMaterial color={lit?'#ffdb82':'#31597b'} emissive={lit?'#ffb84b':'#000000'} emissiveIntensity={lit?.8:0}/></mesh>)}
  <mesh position={[0,-.43,.68]}><boxGeometry args={[.35,.65,.05]}/><meshStandardMaterial color="#43657a"/></mesh>
 </group>;
}
