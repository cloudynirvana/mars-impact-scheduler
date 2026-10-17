import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
export const Root = () => (
  <Composition id="MarsWindows" component={Film} durationInFrames={2910} fps={30} width={1920} height={1080} />
);
