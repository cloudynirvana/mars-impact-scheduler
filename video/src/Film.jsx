import React from 'react';
import {AbsoluteFill, Audio, Img, staticFile, Sequence, useCurrentFrame, interpolate, spring, useVideoConfig, Easing} from 'remotion';
import data from '../public/data.json';

const C = {
  bg: '#07060c', ink: '#f2ece4', dim: '#8d8378', rust: '#e2703a', sand: '#f0b429',
  ice: '#58b0ff', good: '#49d49d', line: '#3a3330',
};
const font = 'Inter, "Helvetica Neue", Arial, sans-serif';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const fade = (f, d) => interpolate(f, [0, 18, d - 18, d], [0, 1, 1, 0], clamp);
const ease = Easing.inOut(Easing.cubic);

const Stars = () => {
  const f = useCurrentFrame();
  const stars = React.useMemo(() => Array.from({length: 150}, (_, i) => {
    const a = Math.sin(i * 912.7) * 10000, b = Math.sin(i * 41.3) * 10000;
    return {x: (a - Math.floor(a)) * 1920, y: (b - Math.floor(b)) * 1080, s: 1 + (i % 3)};
  }), []);
  return <AbsoluteFill style={{background: `radial-gradient(ellipse at 70% 0%, #241109 0%, ${C.bg} 55%)`}}>
    {stars.map((s, i) => <div key={i} style={{position: 'absolute', left: s.x, top: s.y, width: s.s, height: s.s,
      borderRadius: 9, background: '#fff', opacity: 0.2 + 0.45 * Math.abs(Math.sin(f / 40 + i))}} />)}
  </AbsoluteFill>;
};

const Rise = ({children, delay = 0, y = 26}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 200}});
  return <div style={{opacity: s, transform: `translateY(${(1 - s) * y}px)`}}>{children}</div>;
};
const H1 = ({children, size = 62, color = C.ink, weight = 700}) =>
  <div style={{fontFamily: font, fontSize: size, fontWeight: weight, color, letterSpacing: -1.2, lineHeight: 1.15}}>{children}</div>;
const Sub = ({children, size = 30, color = C.dim}) =>
  <div style={{fontFamily: font, fontSize: size, fontWeight: 500, color, lineHeight: 1.35}}>{children}</div>;

// ---------------------------------------------------------------- 1. the window opens
const Orbits = ({d}) => {
  const f = useCurrentFrame();
  const t = f / 30;
  const pt = (r, period, phase) => [960 + r * Math.cos(2 * Math.PI * t / period + phase),
                                    540 + r * Math.sin(2 * Math.PI * t / period + phase) * 0.42];
  const [ex, ey] = pt(230, 6, 0);
  const [mx, my] = pt(355, 11.3, 0.9);
  const sep = Math.atan2(my - 540, mx - 960) - Math.atan2(ey - 540, ex - 960);
  const aligned = Math.abs(((sep + Math.PI) % (2 * Math.PI)) - Math.PI) < 0.45;
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <ellipse cx="960" cy="540" rx="230" ry="96" fill="none" stroke={C.line} strokeWidth="1.5" />
      <ellipse cx="960" cy="540" rx="355" ry="149" fill="none" stroke={C.line} strokeWidth="1.5" />
      <circle cx="960" cy="540" r="17" fill="#ffd166" />
      <circle cx="960" cy="540" r="40" fill="#ffd166" opacity="0.12" />
      {aligned && <line x1={ex} y1={ey} x2={mx} y2={my} stroke={C.sand} strokeWidth="2" opacity="0.65" strokeDasharray="7 7" />}
      <circle cx={ex} cy={ey} r="11" fill={C.ice} />
      <circle cx={mx} cy={my} r="9" fill={C.rust} />
    </svg>
    <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center'}}>
      <Rise><H1 size={72}>Every 26 months, a door opens.</H1></Rise>
      <div style={{height: 18}} />
      <Rise delay={18}><Sub size={32}>Earth catches up with Mars, and the trip is cheap for a few weeks.</Sub></Rise>
    </div>
    <div style={{position: 'absolute', bottom: 120, width: '100%', textAlign: 'center',
      opacity: aligned ? 1 : 0.15, transition: 'none'}}>
      <Sub size={34} color={C.sand}>window open</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 2. the search
const Search = ({d}) => {
  const f = useCurrentFrame();
  const shown = Math.round(interpolate(f, [25, 150], [0, data.n_transfers], clamp));
  return <AbsoluteFill style={{opacity: fade(f, d), alignItems: 'center', justifyContent: 'center'}}>
    {Array.from({length: 34}, (_, i) =>
      <div key={i} style={{position: 'absolute', left: (i * 61) % 1920, fontFamily: 'monospace', fontSize: 16, color: C.rust,
        opacity: 0.3, top: ((f * (6 + i % 6) + i * 131) % 1400) - 200}}>
        {(Math.sin(i * 7.1 + f * 0.02) * 1.5e8).toFixed(0)}
      </div>)}
    <Rise><Sub size={32}>NASA / JPL Horizons · the ephemeris used to fly real spacecraft</Sub></Rise>
    <div style={{height: 26}} />
    <Rise delay={14}><H1 size={56}>Every departure date. Every flight time.</H1></Rise>
    <div style={{height: 44}} />
    <div style={{fontFamily: font, fontSize: 150, fontWeight: 800, color: C.sand, letterSpacing: -4}}>
      {shown.toLocaleString('en-US')}
    </div>
    <Sub size={34}>workable trajectories, 2028 to 2037</Sub>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 3. the porkchop
const PORK = {x0: 250, x1: 1700, y0: 880, y1: 300, t0: 2028.6, t1: 2036.1, f0: 110, f1: 410};
const px = (yr) => PORK.x0 + (yr - PORK.t0) / (PORK.t1 - PORK.t0) * (PORK.x1 - PORK.x0);
const py = (tof) => PORK.y0 + (tof - PORK.f0) / (PORK.f1 - PORK.f0) * (PORK.y1 - PORK.y0);
const c3Colour = (c3) => {
  const t = interpolate(c3, [7, 25], [0, 1], clamp);
  return `rgb(${Math.round(240 - 60 * t)}, ${Math.round(190 - 120 * t)}, ${Math.round(60 + 60 * t)})`;
};

const Porkchop = ({d}) => {
  const f = useCurrentFrame();
  const n = Math.round(interpolate(f, [10, 110], [0, data.porkchop.length], {...clamp, easing: ease}));
  const label = interpolate(f, [125, 150], [0, 1], clamp);
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 70, left: 250}}>
      <Rise><H1 size={54}>They fall into exactly four windows.</H1></Rise>
    </div>
    <svg width="1920" height="1080">
      <line x1={PORK.x0} y1={PORK.y0} x2={PORK.x1} y2={PORK.y0} stroke={C.line} strokeWidth="2" />
      <line x1={PORK.x0} y1={PORK.y0} x2={PORK.x0} y2={PORK.y1} stroke={C.line} strokeWidth="2" />
      {data.porkchop.slice(0, n).map(([yr, tof, c3], i) =>
        <circle key={i} cx={px(yr)} cy={py(tof)} r="2.6" fill={c3Colour(c3)} opacity="0.85" />)}
      {[2029, 2031, 2033, 2035].map(y =>
        <text key={y} x={px(y)} y={PORK.y0 + 34} fill={C.dim} fontSize="22" fontFamily={font} textAnchor="middle">{y}</text>)}
      {[150, 250, 350].map(t =>
        <text key={t} x={PORK.x0 - 18} y={py(t) + 7} fill={C.dim} fontSize="20" fontFamily={font} textAnchor="end">{t} d</text>)}
      {data.windows.map((w, i) => {
        const x = px(2028.92 + i * 2.17);
        return <g key={i} opacity={label}>
          <rect x={x - 62} y={PORK.y1 - 70} width="124" height="44" rx="10" fill="none" stroke={C.sand} strokeWidth="1.5" />
          <text x={x} y={PORK.y1 - 40} fill={C.sand} fontSize="24" fontFamily={font} textAnchor="middle" fontWeight="700">
            {w.departs.slice(0, 4)}
          </text>
        </g>;
      })}
      <text x={PORK.x0} y={PORK.y0 + 76} fill={C.dim} fontSize="22" fontFamily={font}>departure date</text>
      <text x={PORK.x0 - 18} y={PORK.y1 - 24} fill={C.dim} fontSize="22" fontFamily={font} textAnchor="end">flight time</text>
    </svg>
    <div style={{position: 'absolute', bottom: 66, left: 250, opacity: label}}>
      <Sub size={32} color={C.ink}>Miss one and you wait two years.</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 4. the trade
const Bar = ({label, value, max, unit, colour, delay, highlight}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 40}});
  return <div style={{display: 'flex', alignItems: 'center', gap: 18, margin: '11px 0', fontFamily: font}}>
    <div style={{width: 128, fontSize: 25, color: highlight ? C.ink : C.dim, fontWeight: highlight ? 700 : 500}}>{label}</div>
    <div style={{height: 26, width: 300 * (value / max) * s, borderRadius: 7, background: colour,
      boxShadow: highlight ? `0 0 26px ${colour}` : 'none', opacity: highlight ? 1 : 0.4}} />
    <div style={{fontSize: 24, color: highlight ? colour : C.dim, fontWeight: 700}}>{(value * s).toFixed(1)}{unit}</div>
  </div>;
};

const Trade = ({d}) => {
  const f = useCurrentFrame();
  const w = data.windows;
  return <AbsoluteFill style={{opacity: fade(f, d), padding: '96px 150px'}}>
    <Rise><H1 size={54}>Cheap to leave, or cheap to arrive.</H1></Rise>
    <div style={{height: 20}} />
    <Rise delay={12}><Sub>You do not get both in the same window.</Sub></Rise>
    <div style={{display: 'flex', gap: 170, marginTop: 64}}>
      <div>
        <Sub size={28} color={C.ink}>Launch energy needed</Sub>
        <div style={{height: 16}} />
        {w.map((x, i) => <Bar key={i} label={x.departs.slice(0, 7)} value={x.c3} max={15} unit=" km²/s²"
          colour={C.sand} delay={26 + i * 9} highlight={x.c3 === Math.min(...w.map(y => y.c3))} />)}
        <div style={{height: 10}} />
        <Sub size={23}>2033 is the cheapest to leave on</Sub>
      </div>
      <div>
        <Sub size={28} color={C.ink}>Speed hitting the atmosphere</Sub>
        <div style={{height: 16}} />
        {w.map((x, i) => <Bar key={i} label={x.arrives.slice(0, 7)} value={x.entry} max={8} unit=" km/s"
          colour={C.ice} delay={70 + i * 9} highlight={x.entry === Math.min(...w.map(y => y.entry))} />)}
        <div style={{height: 10}} />
        <Sub size={23}>2035 arrives 1.6 km/s slower — a far easier entry</Sub>
      </div>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- Mars globe
const Globe = ({cx, cy, r, spin, marker}) => (
  <g>
    <defs>
      <radialGradient id="mars" cx="35%" cy="30%">
        <stop offset="0%" stopColor="#e8834c" /><stop offset="70%" stopColor="#b8512a" /><stop offset="100%" stopColor="#5e2412" />
      </radialGradient>
      <clipPath id="globeclip"><circle cx={cx} cy={cy} r={r} /></clipPath>
    </defs>
    <circle cx={cx} cy={cy} r={r} fill="url(#mars)" />
    <g clipPath="url(#globeclip)" opacity="0.5">
      {[-60, -30, 0, 30, 60].map(lat => {
        const y = cy - r * Math.sin(lat * Math.PI / 180);
        const rx = r * Math.cos(lat * Math.PI / 180);
        return <ellipse key={lat} cx={cx} cy={y} rx={rx} ry={rx * 0.16} fill="none" stroke="#2b0f07" strokeWidth="1.2" />;
      })}
      {Array.from({length: 12}, (_, i) => {
        const a = ((spin + i * 30) % 360) * Math.PI / 180;
        return <ellipse key={i} cx={cx} cy={cy} rx={Math.abs(r * Math.cos(a))} ry={r}
          fill="none" stroke="#2b0f07" strokeWidth="1.2" opacity={Math.cos(a) > -0.1 ? 0.9 : 0.25} />;
      })}
    </g>
    <circle cx={cx} cy={cy} r={r} fill="none" stroke="#ffb48a" strokeWidth="1" opacity="0.5" />
    {marker}
  </g>
);

// ---------------------------------------------------------------- 5. the approach is locked
const Locked = ({d}) => {
  const f = useCurrentFrame();
  const grow = interpolate(f, [15, 70], [0, 1], {...clamp, easing: ease});
  const spin = f * 1.6;
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080">
      <Globe cx={1300} cy={560} r={250} spin={spin} marker={
        <circle cx={1300 - 250 * 0.999} cy={560} r="11" fill={C.sand} opacity={interpolate(f, [60, 85], [0, 1], clamp)} />} />
      <line x1={380} y1={560} x2={380 + 620 * grow} y2={560} stroke={C.ice} strokeWidth="4" />
      <polygon points={`${380 + 620 * grow},560 ${365 + 620 * grow},549 ${365 + 620 * grow},571`} fill={C.ice} opacity={grow} />
      <text x={400} y={520} fill={C.ice} fontSize="27" fontFamily={font}>arrival direction: locked by the orbit</text>
    </svg>
    <div style={{position: 'absolute', top: 110, left: 150, width: 820}}>
      <Rise><H1 size={54}>The approach is fixed.</H1></Rise>
      <div style={{height: 22}} />
      <Rise delay={16}><Sub size={31}>Once the trajectory is chosen, you arrive from one direction
        and nothing changes it.</Sub></Rise>
      <div style={{height: 30}} />
      <Rise delay={46}><Sub size={37} color={C.rust}>But Mars is still turning. 14.6° every hour.</Sub></Rise>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 6. longitude is free
const Longitude = ({d}) => {
  const f = useCurrentFrame();
  const hours = interpolate(f, [20, 200], [0, 24.6], {...clamp, easing: Easing.inOut(Easing.quad)});
  const lon = (360 - hours * 14.62) % 360;
  const spin = hours * 14.62;
  const names = [[20, 'Chryse'], [90, 'Isidis'], [136, 'Elysium'], [196, 'Amazonis'], [290, 'Tharsis']];
  const near = names.find(([l]) => Math.abs(((lon - l + 180) % 360) - 180) < 20);
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080">
      <Globe cx={700} cy={560} r={280} spin={spin} marker={<g>
        <circle cx={700 - 280} cy={560} r="13" fill={C.sand} />
        <circle cx={700 - 280} cy={560} r={22 + 7 * Math.sin(f / 5)} fill="none" stroke={C.sand} strokeWidth="2" opacity="0.6" />
      </g>} />
      <line x1={180} y1={560} x2={400} y2={560} stroke={C.ice} strokeWidth="4" />
      <polygon points="400,560 385,549 385,571" fill={C.ice} />
    </svg>
    <div style={{position: 'absolute', top: 150, left: 1130, width: 680}}>
      <Rise><H1 size={54}>So the longitude is free.</H1></Rise>
      <div style={{height: 26}} />
      <Rise delay={16}><Sub size={30}>Shift the arrival by a few hours and the same trajectory
        lands on a different continent.</Sub></Rise>
      <div style={{height: 54}} />
      <div style={{fontFamily: font}}>
        <Sub size={25}>arrival shifted by</Sub>
        <div style={{fontSize: 92, fontWeight: 800, color: C.ink, letterSpacing: -2}}>
          {hours.toFixed(1)} <span style={{fontSize: 40, color: C.dim}}>hours</span></div>
        <div style={{height: 26}} />
        <Sub size={25}>impact longitude</Sub>
        <div style={{fontSize: 92, fontWeight: 800, color: C.sand, letterSpacing: -2}}>
          {lon.toFixed(0)}°<span style={{fontSize: 36, color: C.dim}}> E</span></div>
        <div style={{height: 18, fontSize: 32, color: C.rust, fontWeight: 600}}>{near ? `over ${near[1]}` : ''}</div>
      </div>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 7. latitude costs
const Latitude = ({d}) => {
  const f = useCurrentFrame();
  const swing = interpolate(f, [25, 120], [0, 60], {...clamp, easing: ease});
  const a = swing * Math.PI / 180;
  const cx = 1150, cy = 560, r = 250;
  const hit = [cx - r * Math.cos(a), cy - r * Math.sin(a)];
  const path = `M 220 ${cy + 300} Q ${cx - 520} ${cy + 170} ${hit[0]} ${hit[1]}`;
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080">
      <Globe cx={cx} cy={cy} r={r} spin={0} marker={<circle cx={hit[0]} cy={hit[1]} r="11" fill={C.sand} />} />
      <line x1={220} y1={cy} x2={cx - r - 30} y2={cy} stroke={C.line} strokeWidth="2" strokeDasharray="8 8" />
      <path d={path} fill="none" stroke={C.ice} strokeWidth="4" />
      <text x={250} y={cy - 24} fill={C.dim} fontSize="24" fontFamily={font}>dead centre</text>
      <text x={250} y={cy + 345} fill={C.ice} fontSize="24" fontFamily={font}>aimed off centre — gravity bends it round</text>
    </svg>
    <div style={{position: 'absolute', top: 120, left: 150, width: 760}}>
      <Rise><H1 size={54}>Latitude is what you pay for.</H1></Rise>
      <div style={{height: 24}} />
      <Rise delay={16}><Sub size={30}>You buy it by aiming off centre and letting Mars's gravity
        curve you around.</Sub></Rise>
      <div style={{height: 50}} />
      <div style={{fontFamily: font, fontSize: 96, fontWeight: 800, color: C.ice}}>{swing.toFixed(0)}°</div>
      <Sub size={26}>of steering — up to {Math.max(...data.windows.map(w => w.reach))}° is reachable</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 8. the Hellas problem
const Hellas = ({d}) => {
  const f = useCurrentFrame();
  const rows = Object.entries(data.steering).map(([name, v]) => ({name, lat: v.lat, mean: v.swing.reduce((a, b) => a + b) / v.swing.length}))
    .sort((a, b) => a.mean - b.mean);
  const depth = interpolate(f, [150, 210], [0, 1], {...clamp, easing: ease});
  return <AbsoluteFill style={{opacity: fade(f, d), padding: '80px 140px'}}>
    <Rise><H1 size={52}>Which leaves one awkward result.</H1></Rise>
    <div style={{display: 'flex', gap: 110, marginTop: 50}}>
      <div style={{width: 760}}>
        <Sub size={27} color={C.ink}>Steering needed, averaged over the four windows</Sub>
        <div style={{height: 20}} />
        {rows.map((r, i) => {
          const s = interpolate(f, [26 + i * 8, 56 + i * 8], [0, 1], clamp);
          const worst = r.name.startsWith('Hellas');
          return <div key={r.name} style={{display: 'flex', alignItems: 'center', gap: 14, margin: '9px 0', fontFamily: font}}>
            <div style={{width: 225, fontSize: 23, color: worst ? C.rust : C.dim, fontWeight: worst ? 700 : 500}}>{r.name}</div>
            <div style={{width: 74, fontSize: 20, color: C.dim}}>{r.lat.toFixed(0)}°</div>
            <div style={{height: 22, width: 330 * (r.mean / 65) * s, borderRadius: 6,
              background: worst ? C.rust : C.good, opacity: worst ? 1 : 0.55,
              boxShadow: worst ? `0 0 24px ${C.rust}` : 'none'}} />
            <div style={{fontSize: 22, color: worst ? C.rust : C.dim, fontWeight: 700}}>{(r.mean * s).toFixed(0)}°</div>
          </div>;
        })}
      </div>
      <div style={{width: 700, opacity: depth}}>
        <Sub size={27} color={C.ink}>Yet Hellas is the best place to arrive</Sub>
        <svg width="660" height="260" style={{marginTop: 20}}>
          <line x1="20" y1="70" x2="640" y2="70" stroke={C.line} strokeWidth="2" strokeDasharray="6 6" />
          <text x="20" y="56" fill={C.dim} fontSize="20" fontFamily={font}>datum</text>
          <path d="M 20 70 L 180 70 Q 330 250 480 70 L 640 70" fill="#2a1109" stroke={C.rust} strokeWidth="3" />
          <line x1="330" y1="70" x2="330" y2="212" stroke={C.sand} strokeWidth="2" />
          <text x="348" y="150" fill={C.sand} fontSize="30" fontFamily={font} fontWeight="700">6.2 km deep</text>
        </svg>
        <div style={{marginTop: 10}}>
          <Sub size={31} color={C.ice}>1.7× the air to brake against</Sub>
          <div style={{height: 8}} />
          <Sub size={24}>You have to shed 6 km/s. Hellas gives you the most air to do it in.</Sub>
        </div>
      </div>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 9. close
const End = ({d}) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(f, [0, 20], [0, 1], clamp), justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
    <Rise><H1 size={64}>The trajectory wants the equator.</H1></Rise>
    <div style={{height: 14}} />
    <Rise delay={22}><H1 size={64} color={C.rust}>The entry physics wants Hellas.</H1></Rise>
    <div style={{height: 36}} />
    <Rise delay={46}><Sub size={36} color={C.ink}>Somebody has to choose.</Sub></Rise>
    <div style={{height: 80}} />
    <Rise delay={70}><Sub size={23}>
      JPL Horizons ephemerides · MOLA topography · Lambert transfers, IAU Mars rotation
      <br />Rotation model checked against JPL to 0.007° — about 400 m on the ground
    </Sub></Rise>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- assembly
const SCENES = [
  [Orbits, 240], [Search, 270], [Porkchop, 300], [Trade, 480],
  [Locked, 330], [Longitude, 270], [Latitude, 210], [Hellas, 570], [End, 240],
];

export const Film = () => {
  let at = 0;
  return <AbsoluteFill style={{background: C.bg}}>
    <Stars />
    <Audio src={staticFile('soundtrack.wav')} />
    {SCENES.map(([S, d], i) => {
      const from = at; at += d;
      return <Sequence key={i} from={from} durationInFrames={d}><S d={d} /></Sequence>;
    })}
  </AbsoluteFill>;
};
