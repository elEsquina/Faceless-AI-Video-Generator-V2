import React from 'react';
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { gsap } from 'gsap';

export const MainScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const timeline = gsap.timeline({ paused: true });
  const state = { rot: 0, powerPulse: 1.0 };
  timeline.to(state, { rot: 0.6, powerPulse: 2.0, duration: 3.5, ease: 'power1.inOut' }, 0);
  timeline.seek(frame / fps);

  return (
    <AbsoluteFill style={{ backgroundColor: '#090d16' }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, 5.2], fov: 45 }}>
        <ambientLight intensity={0.8} />
        <directionalLight position={[5, 5, 4]} intensity={2.2} />
        {/* Inverter module */}
        <mesh position={[-1.2, 0, 0]} rotation={[0.2, state.rot, 0]}>
          <boxGeometry args={[1.5, 1.8, 0.5]} />
          <meshStandardMaterial color="#334155" metalness={0.6} roughness={0.3} />
        </mesh>
        {/* Battery energy storage */}
        <mesh position={[1.4, 0, 0]} rotation={[0.2, -state.rot * 0.5, 0]}>
          <cylinderGeometry args={[0.7, 0.7, 1.8, 24]} />
          <meshStandardMaterial color="#16a34a" emissive="#15803d" emissiveIntensity={state.powerPulse * 0.3} />
        </mesh>
      </ThreeCanvas>
      <div style={{ position: 'absolute', top: 50, left: 60, fontFamily: 'sans-serif' }}>
        <h2 style={{ color: '#4ade80', fontSize: 40, margin: 0 }}>
          Inverter & Grid Power
        </h2>
        <p style={{ color: '#cbd5e1', fontSize: 24, marginTop: 8 }}>
          Inverters convert DC to AC electricity, powering homes 24/7
        </p>
      </div>
    </AbsoluteFill>
  );
};
export default MainScene;
