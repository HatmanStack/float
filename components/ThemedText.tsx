import React from 'react';
import { Text, type TextProps, StyleSheet, Platform, useWindowDimensions } from 'react-native';

import { useThemeColor } from '@/hooks/useThemeColor';

/**
 * Props for ThemedText component
 */
export interface ThemedTextProps extends TextProps {
  lightColor?: string;
  darkColor?: string;
  type?:
    | 'default'
    | 'title'
    | 'subtitle'
    | 'incidentSubtitle'
    | 'generate'
    | 'link'
    | 'header'
    | 'details'
    | 'incidentDetails';
}

/**
 * A Text component that adapts to the current theme colors and provides consistent typography
 */
export function ThemedText({
  style,
  lightColor,
  darkColor,
  type = 'default',
  ...rest
}: ThemedTextProps): React.JSX.Element {
  const color = useThemeColor({ light: lightColor, dark: darkColor }, 'text');
  const window = useWindowDimensions();

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
        lineHeight: 20 * scale,
      },
      subtitle: {
        fontSize: 15 * scale,
        fontWeight: 'bold',
      },
      incidentSubtitle: {
        fontSize: 15 * scale,
        fontWeight: 'bold',
        color: '#fffff2',
      },
      generate: {
        lineHeight: 15 * scale,
        fontSize: 15 * scale,
        fontWeight: 'bold',

        color: '#fffff2',
        textAlign: 'center',
      },
      header: {
        fontSize: 75 * scale,
        lineHeight: Platform.select({
          web: 30 * scale,
          android: 175,
          default: 50,
        }),
        fontFamily: 'Logo',
      },
      details: {
        fontSize: 12 * scale,
        flexWrap: 'wrap',
        fontWeight: 'normal',
      },
      incidentDetails: {
        fontSize: 12 * scale,
        flexWrap: 'wrap',
        fontWeight: 'normal',
        color: '#fffff2',
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
        type === 'incidentSubtitle' ? styles.incidentSubtitle : undefined,
        type === 'generate' ? styles.generate : undefined,
        type === 'link' ? styles.link : undefined,
        type === 'header' ? styles.header : undefined,
        type === 'details' ? styles.details : undefined,
        type === 'incidentDetails' ? styles.incidentDetails : undefined,
        style,
      ]}
      {...rest}
    />
  );
}
