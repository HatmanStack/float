import { ScrollViewStyleReset } from 'expo-router/html';
import { type PropsWithChildren } from 'react';

/**
 * This file is web-only and used to configure the root HTML for every web page during static rendering.
 * The contents of this function only run in Node.js environments and do not have access to the DOM or browser APIs.
 */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />

        {/* SEO Meta Tags */}
        <title>Float - From Feelings to Flow | Personalized Meditations</title>
        <meta name="description" content="Transform your emotions into personalized guided meditations. Record how you feel and let AI create a calming meditation experience tailored just for you." />
        <meta name="keywords" content="meditation, mindfulness, emotions, mental health, guided meditation, AI meditation, personalized meditation" />
        <meta name="author" content="HatStack" />
        <link rel="canonical" href="https://float.hatstack.fun/" />
        <meta name="robots" content="index, follow" />
        <meta name="theme-color" content="#A1BE95" />

        {/* Open Graph */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://float.hatstack.fun/" />
        <meta property="og:title" content="Float - From Feelings to Flow | Personalized Meditations" />
        <meta property="og:description" content="Transform your emotions into personalized guided meditations. Record how you feel and let AI create a calming meditation experience tailored just for you." />
        <meta property="og:image" content="https://float.hatstack.fun/og-image.jpg" />
        <meta property="og:site_name" content="Float" />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content="https://float.hatstack.fun/" />
        <meta name="twitter:title" content="Float - From Feelings to Flow | Personalized Meditations" />
        <meta name="twitter:description" content="Transform your emotions into personalized guided meditations. Record how you feel and let AI create a calming meditation experience tailored just for you." />
        <meta name="twitter:image" content="https://float.hatstack.fun/og-image.jpg" />

        {/* Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebApplication',
              name: 'Float',
              description: 'Transform your emotions into personalized guided meditations',
              url: 'https://float.hatstack.fun',
              applicationCategory: 'HealthApplication',
              operatingSystem: 'Web, iOS, Android',
              offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
            }),
          }}
        />

        {/*
          Disable body scrolling on web. This makes ScrollView components work closer to how they do on native.
          However, body scrolling is often nice to have for mobile web. If you want to enable it, remove this line.
        */}
        <ScrollViewStyleReset />

        {/* Using raw CSS styles as an escape-hatch to ensure the background color never flickers in dark-mode. */}
        <style dangerouslySetInnerHTML={{ __html: responsiveBackground }} />
      </head>
      <body>{children}</body>
    </html>
  );
}

const responsiveBackground = `
body {
  background-color: #fff;
}
@media (prefers-color-scheme: dark) {
  body {
    background-color: #000;
  }
}`;
