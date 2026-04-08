// Hand-written color palette replacing the 3888-line generated gradient file.
// See docs/plans/2026-04-08-audit-float/Phase-1.md Task 1.
//
// Public shape is preserved: `Colors.<emotion>.{one,two,three,four,five}` is
// still a `string[]`. Consumers in `IncidentColoring.tsx` slice these arrays
// starting from a computed `colorKey`; a short gradient is sufficient because
// the slice gracefully returns fewer elements near the end.
//
// Each emotion gradient transitions from a characteristic starting color to
// the shared calm-green endpoint `#1ce815`. The five intensity variants reuse
// the same base palette; the original file had a longer gradient per intensity
// level but consumers do not distinguish lengths beyond the leading index.

const tintColorLight = '#60465a';
const tintColorDark = '#fff';

const gradient = (...stops: string[]): string[] => stops;

const angryPalette = gradient(
  '#ff0000',
  '#e51902',
  '#cc3304',
  '#b34d07',
  '#9a6709',
  '#80800b',
  '#679a0e',
  '#4eb410',
  '#35ce12',
  '#1ce815'
);

const disgustedPalette = gradient(
  '#6a4a3a',
  '#615b35',
  '#586d31',
  '#4b872b',
  '#3ea125',
  '#31bc1f',
  '#24d619',
  '#1ce815'
);

const happyPalette = gradient(
  '#fdda0d',
  '#e4db0d',
  '#cbdd0e',
  '#b2de0f',
  '#99e010',
  '#80e111',
  '#67e312',
  '#4ee413',
  '#35e614',
  '#1ce815'
);

const sadPalette = gradient(
  '#1434a4',
  '#144894',
  '#15528c',
  '#155c84',
  '#167074',
  '#178464',
  '#188e5c',
  '#1aa244',
  '#1bc02c',
  '#1ce815'
);

const surprisedPalette = gradient(
  '#ff7518',
  '#e58117',
  '#cc8e17',
  '#b39b17',
  '#9aa816',
  '#80b515',
  '#67c214',
  '#4ed014',
  '#35dd14',
  '#1ce815'
);

const fearfulPalette = gradient(
  '#353935',
  '#324c31',
  '#2f5f2d',
  '#2c732a',
  '#298626',
  '#249b21',
  '#20b01d',
  '#1bc518',
  '#1ce815'
);

const neutralPalette = gradient(
  '#808588',
  '#789080',
  '#709c77',
  '#68a86e',
  '#5eb561',
  '#4ec54f',
  '#3dd53a',
  '#28e120',
  '#1ce715'
);

const emotion = (palette: string[]) => ({
  one: palette,
  two: palette,
  three: palette,
  four: palette,
  five: palette,
});

export const Colors = {
  buttonUnpressed: '#747c65',
  buttonPressed: '#60465a',
  activityIndicator: '#a18da5',
  light: {
    text: '#11181C',
    background: '#d1d5eb',
    tint: tintColorLight,
    icon: '#687076',
    tabIconDefault: '#687076',
    tabIconSelected: tintColorLight,
  },
  dark: {
    text: '#ECEDEE',
    background: '#525668',
    tint: tintColorDark,
    icon: '#9BA1A6',
    tabIconDefault: '#9BA1A6',
    tabIconSelected: tintColorDark,
  },
  angry: emotion(angryPalette),
  disgusted: emotion(disgustedPalette),
  happy: emotion(happyPalette),
  sad: emotion(sadPalette),
  surprised: emotion(surprisedPalette),
  fearful: emotion(fearfulPalette),
  neutral: emotion(neutralPalette),
};
