import React from 'react';
import {Composition} from 'remotion';
import {Demo3D} from './scene';
export const Root: React.FC = () => <Composition
  id="Demo3D" component={Demo3D} durationInFrames={30} fps={30} width={640} height={360}
/>;
