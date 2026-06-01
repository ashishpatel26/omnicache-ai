import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'OmniCache-AI',
  tagline: 'Unified multi-layer caching for AI agent pipelines',
  favicon: 'img/omnicache_logo.png',

  url: 'https://ashishpatel26.github.io',
  baseUrl: '/omnicache-ai/',
  organizationName: 'ashishpatel26',
  projectName: 'omnicache-ai',
  trailingSlash: false,
  deploymentBranch: 'gh-pages',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: { defaultLocale: 'en', locales: ['en'] },

  markdown: { mermaid: true },
  themes: [
    '@docusaurus/theme-mermaid',
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        language: ['en'],
        indexDocs: true,
        indexBlog: false,
        docsRouteBasePath: '/docs',
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
        searchBarShortcut: true,
        searchBarShortcutHint: true,
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/ashishpatel26/omnicache-ai/tree/main/website/',
          routeBasePath: 'docs',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/omnicache_logo.png',
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'OmniCache-AI',
      logo: {
        alt: 'OmniCache-AI',
        src: 'img/omnicache_logo.png',
        width: 32,
        height: 32,
      },
      style: 'dark',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        { to: '/docs/cookbook', label: 'Cookbook', position: 'left' },
        { to: '/docs/api-reference', label: 'API Reference', position: 'left' },
        {
          href: 'https://github.com/ashishpatel26/omnicache-ai',
          position: 'right',
          className: 'header-github-link',
          'aria-label': 'GitHub',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Getting Started', to: '/docs/getting-started/installation' },
            { label: 'Core', to: '/docs/core' },
            { label: 'Backends', to: '/docs/backends' },
            { label: 'Cache Layers', to: '/docs/layers' },
          ],
        },
        {
          title: 'Integrations',
          items: [
            { label: 'Adapters', to: '/docs/adapters' },
            { label: 'Middleware', to: '/docs/middleware' },
            { label: 'Cookbook', to: '/docs/cookbook' },
          ],
        },
        {
          title: 'Reference',
          items: [
            { label: 'API Reference', to: '/docs/api-reference' },
            { label: 'GitHub', href: 'https://github.com/ashishpatel26/omnicache-ai' },
            { label: 'PyPI', href: 'https://pypi.org/project/omnicache-ai/' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} OmniCache-AI Contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.dracula,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'json', 'yaml', 'toml'],
    },
    mermaid: {
      theme: { light: 'dark', dark: 'dark' },
    },
  } satisfies Preset.ThemeConfig,

  headTags: [
    {
      tagName: 'link',
      attributes: {
        rel: 'preconnect',
        href: 'https://fonts.googleapis.com',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'preconnect',
        href: 'https://fonts.gstatic.com',
        crossorigin: 'anonymous',
      },
    },
    {
      tagName: 'link',
      attributes: {
        href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap',
        rel: 'stylesheet',
      },
    },
  ],
};

export default config;
