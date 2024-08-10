// You can explore the built-in icon families and icons on the web at https://icons.expo.fyi/

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import MaterialIconsProps from '@expo/vector-icons/build/createIconSet';
import { type ComponentProps } from 'react';

export function TabBarIcon({ style, ...rest }: MaterialIcons<ComponentProps<typeof MaterialIconsProps>['name']>) {
  return <MaterialIcons size={28} style={[{ marginBottom: -3 }, style]} {...rest} />;
}
