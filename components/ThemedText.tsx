import { Text, type TextProps, StyleSheet, Dimensions } from 'react-native';

import { useThemeColor } from '@/hooks/useThemeColor';

export type ThemedTextProps = TextProps & {
  lightColor?: string;
  darkColor?: string;
  type?: 'default' | 'title' | 'subtitle' | 'generate' | 'link' | 'header' | 'details';
};

export function ThemedText({
  style,
  lightColor,
  darkColor,
  type = 'default',
  ...rest
}: ThemedTextProps) {
  const color = useThemeColor({ light: lightColor, dark: darkColor }, 'text');
  const window = Dimensions.get('window');

  const getStyles = () => {
    const baseWidth = 500; 
    
    let scale = window.width / baseWidth;
    scale = Math.min(Math.max(scale, 1), 1.58);
    
    
    return StyleSheet.create({
      default: {
        fontSize: 4 * scale,
        lineHeight: 6 * scale,
      },
      title: {
        fontSize: 20 * scale,
        fontWeight: 'bold',
        lineHeight: 15 * scale,
      },
      subtitle: {
        fontSize: 15 * scale,
        fontWeight: 'bold',
      },
      generate: {
        lineHeight: 15 * scale,
        fontSize: 15 * scale,
        fontWeight: 'bold',
        textAlign: 'center',
      },
      link: {
        lineHeight: 8 * scale,
        fontSize: 4 * scale,
        color: '#0a7ea4',
      },
      header: {
        fontSize: 75 * scale,
        lineHeight: 8 * scale,
        fontFamily: 'Logo',
      },
      details: {
        fontSize: 12 * scale,
        flexWrap: 'wrap',
        fontWeight: 'normal',
      },
    });
  };

  const styles = getStyles();

  return (
    <Text
      style={[
        { color },
        type === 'default' ? styles.default : undefined,
        type === 'title' ? styles.title : undefined,
        type === 'subtitle' ? styles.subtitle : undefined,
        type === 'generate' ? styles.generate : undefined,
        type === 'link' ? styles.link : undefined,
        type === 'header' ? styles.header : undefined,
        type === 'details' ? styles.details : undefined,
        style,
      ]}
      {...rest}
    />
  );
}