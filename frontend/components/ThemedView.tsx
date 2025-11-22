import React from 'react';
import { View, type ViewProps } from 'react-native';
import { useThemeColor } from "@/frontend/hooks/useThemeColor';
interface ThemedViewProps extends ViewProps {
  lightColor?: string;
  darkColor?: string;
}
export function ThemedView({
  style,
  lightColor,
  darkColor,
  ...rest
}: ThemedViewProps): React.ReactNode {
  const backgroundColor = useThemeColor({ light: lightColor, dark: darkColor }, 'background');
  return <View style={[{ backgroundColor }, style]} {...rest} />;
}
