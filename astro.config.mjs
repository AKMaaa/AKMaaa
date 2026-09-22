// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	site: 'https://AKMaaa.github.io',
	vite: {
		// Astro 既定は PUBLIC_ のみ。サーバー用 MICROCMS_* も import.meta.env に載せる
		envPrefix: ['PUBLIC_', 'MICROCMS_'],
	},
});
