import React from 'react';
import {Composition} from 'remotion';
import {Film, TOTAL} from './Film';
export const Root = () => (
  <Composition id="MarsWindows" component={Film} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
);
