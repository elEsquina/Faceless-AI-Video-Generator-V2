import React from 'react';
import { Composition } from 'remotion';
import { Demo3D } from './scene';
import ActiveScene from './active_scene';

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Demo3D"
        component={Demo3D}
        durationInFrames={30}
        fps={30}
        width={640}
        height={360}
      />
      <Composition
        id="MainScene"
        component={ActiveScene}
        durationInFrames={1800}
        fps={30}
        width={1280}
        height={720}
      />
    </>
  );
};
