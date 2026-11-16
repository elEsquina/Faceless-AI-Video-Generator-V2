import React from 'react';
import {useCurrentFrame, useVideoConfig, AbsoluteFill} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {gsap} from 'gsap';

// Set timeline to each absolute frame to avoid nondeterministic wall-clock GSAP animations.
export const Demo3D: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const timeline = gsap.timeline({paused: true});
  const position = {rotation: 0};
  timeline.to(position, {rotation: Math.PI * 2, duration: 1, ease: 'none'});
  timeline.seek(frame / fps);
  return <AbsoluteFill style={{backgroundColor: '#101827'}}>
    <ThreeCanvas width={640} height={360} camera={{position: [0, 0, 5], fov: 45}}>
      <ambientLight intensity={0.8}/>
      <directionalLight position={[2, 4, 5]} intensity={2}/>
      <mesh rotation={[0.25, position.rotation, 0]}>
        <boxGeometry args={[1.6, 1.6, 1.6]}/>
        <meshStandardMaterial color="#46c7ff"/>
      </mesh>
    </ThreeCanvas>
  </AbsoluteFill>;
};
