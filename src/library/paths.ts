/** GitHub Pages の `/AKMaaa/` など base を付与する */
export const withBase = (path: string): string => {
	if (!path) return path;
	if (/^(https?:|data:|mailto:)/i.test(path)) return path;
	const base = import.meta.env.BASE_URL || '/';
	const normalized = path.replace(/^\/+/, '');
	return `${base}${normalized}`;
};
