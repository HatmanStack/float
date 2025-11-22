import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React, { type ComponentProps } from 'react';
type TabBarIconProps = ComponentProps<typeof MaterialIcons>;
export function TabBarIcon({ style, ...rest }: TabBarIconProps): React.ReactNode {
  return <MaterialIcons size={28} style={[{ marginBottom: -3 }, style]} {...rest} />;
}
