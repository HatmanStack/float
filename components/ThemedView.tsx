import React from 'react';
import { View, type ViewProps } from 'react-native';

import { useThemeColor } from '@/hooks/useThemeColor';

/**
 * Props for ThemedView component
 */
interface ThemedViewProps extends ViewProps {
  lightColor?: string;
  darkColor?: string;
}

/**
 * A View component that adapts to the current theme colors
 */
export function ThemedView({
  style,
  lightColor,
  darkColor,
  ...rest
}: ThemedViewProps): React.ReactNode {
  const backgroundColor = useThemeColor({ light: lightColor, dark: darkColor }, 'background');

  return <View style={[{ backgroundColor }, style]} {...rest} />;
}
