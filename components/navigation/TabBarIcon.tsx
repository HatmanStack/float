// You can explore the built-in icon families and icons on the web at https://icons.expo.fyi/

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { type ComponentProps } from 'react';

type MaterialIconsProps = ComponentProps<typeof MaterialIcons>;

export function TabBarIcon({ style, ...rest }: MaterialIconsProps) {
  return <MaterialIcons size={28} style={[{ marginBottom: -3 }, style]} {...rest} />;
}