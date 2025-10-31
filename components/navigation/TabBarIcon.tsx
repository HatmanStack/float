// You can explore the built-in icon families and icons on the web at https://icons.expo.fyi/

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React, { type ComponentProps } from 'react';

/**
 * Props for TabBarIcon component
 */
type TabBarIconProps = ComponentProps<typeof MaterialIcons>;

/**
 * Tab bar icon component with consistent styling
 */
export function TabBarIcon({ style, ...rest }: TabBarIconProps): React.ReactNode {
  return <MaterialIcons size={28} style={[{ marginBottom: -3 }, style]} {...rest} />;
}
