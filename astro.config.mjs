// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
// リポジトリ Pages は https://akmaaa.github.io/AKMaaa/ なので base 必須。
// 付けないと CSS/画像がルート参照になりスタイルが消える。
export default defineConfig({
	site: 'https://akmaaa.github.io',
	base: '/AKMaaa/',
	vite: {
		// Astro 既定は PUBLIC_ のみ。サーバー用 MICROCMS_* も import.meta.env に載せる
		envPrefix: ['PUBLIC_', 'MICROCMS_'],
	},
});
