#!/usr/bin/env node
/**
 * Post-export script to inject SEO meta tags into the built index.html
 * Run after `npx expo export --platform web`
 */

const fs = require('fs');
const path = require('path');

const distPath = path.join(__dirname, '..', 'dist', 'index.html');

const seoTags = `
    <!-- Primary Meta Tags -->
    <title>Float - From Feelings to Flow | Personalized Meditations</title>
    <meta name="title" content="Float - From Feelings to Flow | Personalized Meditations" />
    <meta name="description" content="Transform your emotions into personalized guided meditations. Record how you feel and let AI create a calming meditation experience tailored just for you." />
    <meta name="keywords" content="meditation, mindfulness, emotions, mental health, guided meditation, AI meditation, personalized meditation" />
    <meta name="author" content="HatStack" />

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://float.hatstack.fun/" />
    <meta property="og:title" content="Float - From Feelings to Flow | Personalized Meditations" />
    <meta property="og:description" content="Transform your emotions into personalized guided meditations. Record how you feel and let AI create a calming meditation experience tailored just for you." />
    <meta property="og:image" content="https://float.hatstack.fun/og-image.jpg" />
    <meta property="og:site_name" content="Float" />

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:url" content="https://float.hatstack.fun/" />
    <meta name="twitter:title" content="Float - From Feelings to Flow | Personalized Meditations" />
    <meta name="twitter:description" content="Transform your emotions into personalized guided meditations. Record how you feel and let AI create a calming meditation experience tailored just for you." />
    <meta name="twitter:image" content="https://float.hatstack.fun/og-image.jpg" />

    <!-- Additional SEO -->
    <link rel="canonical" href="https://float.hatstack.fun/" />
    <meta name="robots" content="index, follow" />
    <meta name="theme-color" content="#A1BE95" />

    <!-- Structured Data -->
    <script type="application/ld+json">
      {"@context":"https://schema.org","@type":"WebApplication","name":"Float","description":"Transform your emotions into personalized guided meditations","url":"https://float.hatstack.fun","applicationCategory":"HealthApplication","operatingSystem":"Web, iOS, Android","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}}
    </script>
`;

try {
  let html = fs.readFileSync(distPath, 'utf8');

  // Replace the default title and inject SEO tags after viewport meta
  html = html.replace(
    /<title>Float<\/title>/,
    ''
  );

  html = html.replace(
    /<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" \/>/,
    `<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />${seoTags}`
  );

  fs.writeFileSync(distPath, html);
  console.log('SEO tags injected successfully into dist/index.html');
} catch (error) {
  console.error('Error injecting SEO tags:', error.message);
  process.exit(1);
}
