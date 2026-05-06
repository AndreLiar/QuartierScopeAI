import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'QuartierScope AI',
  description:
    'Multi-agent AI copilot for French neighborhood analysis — built for 2-person CGP firms on HubSpot Free.',
  base: '/QuartierScopeAI/',
  cleanUrls: true,
  lastUpdated: true,

  head: [
    ['meta', { name: 'theme-color', content: '#0ea5e9' }],
    ['meta', { property: 'og:title', content: 'QuartierScope AI — Documentation' }],
    [
      'meta',
      {
        property: 'og:description',
        content:
          'Système multi-agents IA pour CGP indépendants. RAG + data.gouv MCP + HubSpot.',
      },
    ],
  ],

  markdown: {
    lineNumbers: false,
  },

  themeConfig: {
    siteTitle: 'QuartierScope AI',
    nav: [
      { text: 'Overview', link: '/overview' },
      { text: 'Architecture', link: '/architecture' },
      { text: 'Sprints', link: '/sprints' },
      { text: 'Journey', link: '/journey' },
      {
        text: 'Repo',
        link: 'https://github.com/AndreLiar/QuartierScopeAI',
      },
    ],

    sidebar: [
      {
        text: 'Project',
        items: [
          { text: 'Home', link: '/' },
          { text: 'Overview & ICP', link: '/overview' },
          { text: 'The 2-sentence pitch', link: '/overview#pitch' },
        ],
      },
      {
        text: 'Engineering',
        items: [
          { text: 'Architecture', link: '/architecture' },
          { text: 'Stack & decisions', link: '/stack' },
          { text: 'Integrations', link: '/integrations' },
          { text: 'Deployment & CI/CD', link: '/deployment' },
        ],
      },
      {
        text: 'Process',
        items: [
          { text: 'Sprints (epics & stories)', link: '/sprints' },
          { text: 'Setup journey & lessons', link: '/journey' },
        ],
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/AndreLiar/QuartierScopeAI' },
    ],

    search: {
      provider: 'local',
    },

    footer: {
      message:
        'Built as a 44h student project — multi-agent AI for CGP firms.',
      copyright: 'MIT licensed',
    },

    editLink: {
      pattern:
        'https://github.com/AndreLiar/QuartierScopeAI/edit/main/docs/:path',
      text: 'Edit this page on GitHub',
    },
  },
})
