import { description } from "../../package";
import { getDirname, path } from "@vuepress/utils";
import { hopeTheme } from "vuepress-theme-hope";
import registerComponentsPlugin from "@vuepress/plugin-register-components";
import { viteBundler } from "@vuepress/bundler-vite";
import { viteStaticCopy } from "vite-plugin-static-copy";


const __dirname = getDirname(import.meta.url);

export default {
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#title
   */
  title: "Fundiverse",
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#description
   */
  description: description,

  /**
   * Extra tags to be injected to the page HTML `<head>`
   *
   * ref：https://v1.vuepress.vuejs.org/config/#head
   */
  head: [
    [
      "link",
      { rel: "apple-touch-icon", sizes: "180x180", href: "/favicon.png" },
    ],
    ["meta", { name: "theme-color", content: "#3eaf7c" }],
    ["meta", { name: "apple-mobile-web-app-capable", content: "yes" }],
    ['link', { rel: 'stylesheet', href:"https://cdn.jsdelivr.net/npm/@mdi/font@5.x/css/materialdesignicons.min.css" }],
    ['link', { rel: 'stylesheet', href:"https://fonts.googleapis.com/icon?family=Material+Icons" }],
    [
      "meta",
      { name: "apple-mobile-web-app-status-bar-style", content: "black" },
    ],
    [
      "script",
      {
        async: true,
        src: "https://www.googletagmanager.com/gtag/js?id=G-53FSTW9NTV",
      },
    ],
    [
      "script",
      {},
      `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

gtag('config', 'G-53FSTW9NTV');
`,
    ],
  ],

  /**
   * Theme configuration, here is the default theme configuration for VuePress.
   *
   * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
   */
  // theme: "vt",
  theme: hopeTheme({
    enableDarkMode: true,
    repo: "https://github.com/greenmtnboy/fundiverse",
    editLinks: false,
    docsDir: "",
    editLinkText: "",
    lastUpdated: false,
    mdEnhance: {
      components: true,
    },
    logo: "/logo-only-transparent-png.png",
    clientConfigFile: path.resolve(__dirname, "./client.ts"),
    displayFooter: true,
    contributors: false,
    meta: {
      contributors: false,
    },
    footer:
      'Not Stock Advice | GPL Licensed | Contributions Welcome | <a href="https://github.com/greenmtnboy/fundiverse">Source</a> | <a href="/tos">Terms of Service</a> | <a href="/privacy">Privacy Policy</a>',
    navbar: [
      {
        text: "About",
        link: "/about/",
      },
      {
        text: "Index Lab/Demo",
        link: "/index_demo/",
      },
      {
        text: "Install",
        link: "/install/",
      },
    ],
    sidebar: {
      "/about/": [],
      "/demo/": [],
      "/install/": [
        {
          text: "Overview",
          path: "/install/",
          collapsable: false,
        },
        {
          text: "Windows",
          path: "windows",
          collapsable: false,
        },
        {
          text: "Mac",
          path: "mac",
          collapsable: false,
        },
        {
          text: "Linux",
          path: "linux",
          collapsable: false,
        },
        {
          text: "First Portfolio",
          path: "first-portfolio",
          collapsable: false,
        },
        {
          text: "Alpaca",
          path: "install-alpaca",
          collapsable: false,
        },
        {
          text: "Robinhood",
          path: "install-robinhood",
          collapsable: false,
        },
        {
          text: "Webull",
          path: "install-webull",
          collapsable: false,
        },
      ],
    },
  }),

  /**
   * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
   */
  plugins: [
    registerComponentsPlugin({
      componentsDir: path.resolve(__dirname, "./components"),
    }),
    "@vuepress/plugin-back-to-top",
    "@vuepress/plugin-medium-zoom",
  ],
  bundler: viteBundler({
    viteOptions: {
      ssr: {
        noExternal: ["vuetify"],
      },
      optimizeDeps: {
        exclude: ["pyodide"],
      },
      plugins: [],
      resolve: {
        alias: {
          "node-fetch": "axios",
        },
      },
    },
    vuePluginOptions: {},
  }),
};
