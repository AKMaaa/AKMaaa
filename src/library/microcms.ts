import { createClient, type MicroCMSQueries } from 'microcms-js-sdk';

export type NewsImage = {
	url: string;
	width?: number;
	height?: number;
	alt?: string;
};

export type News = {
	id: string;
	title: string;
	date: string;
	body?: string;
	link?: string;
	thumbnail?: NewsImage;
	category?: string;
};

export type NewsNeighbor = Pick<News, 'id' | 'title' | 'date' | 'thumbnail'>;

export type Research = {
	id: string;
	title: string;
	date: string;
	venue?: string;
	role?: string;
	author?: string;
	summary?: string;
	link?: string;
};

export type Work = {
	id: string;
	title: string;
	date?: string;
	summary: string;
	stack?: string | string[];
	url?: string;
	repo?: string;
};

/** @deprecated 移行用 */
export type Activity = {
	id: string;
	title: string;
	date: string;
	category?: string[];
	location?: string;
	link?: string;
	content?: string;
};

type MicroCMSImageRaw = {
	url?: string;
	width?: number;
	height?: number;
	alt?: string;
};

type MicroCMSNewsRaw = {
	id: string;
	title: string;
	date?: string;
	publishedAt?: string;
	body?: string;
	content?: string;
	link?: string;
	eyecatch?: MicroCMSImageRaw;
	thumbnail?: MicroCMSImageRaw;
	image?: MicroCMSImageRaw;
	ogimage?: MicroCMSImageRaw;
	category?: string | { name?: string };
};

const readEnv = (name: string): string => {
	const fromMeta = (import.meta.env as Record<string, string | undefined>)[name];
	const fromProcess =
		typeof process !== 'undefined' ? process.env[name] : undefined;
	const value = fromMeta ?? fromProcess ?? '';
	return typeof value === 'string' ? value.trim() : '';
};

const getCredentials = () => {
	const serviceDomain = readEnv('MICROCMS_SERVICE_DOMAIN');
	const apiKey = readEnv('MICROCMS_API_KEY');
	const ok =
		serviceDomain.length > 0 &&
		apiKey.length > 0 &&
		!serviceDomain.startsWith('your-') &&
		!apiKey.startsWith('your-');

	return ok ? { serviceDomain, apiKey } : null;
};

export const hasMicroCMSCredentials = (): boolean => getCredentials() !== null;

const getClient = () => {
	const credentials = getCredentials();
	if (!credentials) return null;
	return createClient(credentials);
};

const warnMissingCredentials = () => {
	console.warn(
		'microCMS の認証情報が未設定です。.env の MICROCMS_SERVICE_DOMAIN と MICROCMS_API_KEY を実値に差し替えてください。',
	);
};

const toImage = (raw?: MicroCMSImageRaw): NewsImage | undefined => {
	if (!raw?.url) return undefined;
	return {
		url: raw.url,
		width: raw.width,
		height: raw.height,
		alt: raw.alt,
	};
};

const firstImageFromHtml = (html?: string): NewsImage | undefined => {
	if (!html) return undefined;
	const match = html.match(/<img[^>]+src=["']([^"']+)["']/i);
	if (!match?.[1]) return undefined;
	return { url: match[1] };
};

const normalizeNews = (item: MicroCMSNewsRaw): News => {
	const body = item.body || item.content;
	const thumbnail =
		toImage(item.eyecatch) ||
		toImage(item.thumbnail) ||
		toImage(item.image) ||
		toImage(item.ogimage) ||
		firstImageFromHtml(body);

	const category =
		typeof item.category === 'string'
			? item.category
			: item.category?.name || undefined;

	return {
		id: item.id,
		title: item.title,
		date: item.date || item.publishedAt || '',
		body,
		link: item.link,
		thumbnail,
		category,
	};
};

const getList = async <T>(
	endpoint: string,
	queries: MicroCMSQueries = {},
): Promise<(T & { id: string })[]> => {
	const client = getClient();
	if (!client) {
		warnMissingCredentials();
		return [];
	}

	try {
		const data = await client.getList<T>({
			endpoint,
			queries: {
				limit: 100,
				...queries,
			},
		});

		return data.contents ?? [];
	} catch (error) {
		console.error(`microCMS からの ${endpoint} 取得に失敗しました:`, error);
		return [];
	}
};

export const getNews = async (queries: MicroCMSQueries = {}): Promise<News[]> => {
	const contents = await getList<MicroCMSNewsRaw>('news', {
		orders: '-publishedAt',
		...queries,
	});

	return contents.map(normalizeNews);
};

/** 1件取得: GET /api/v1/news/{contentId} 相当 */
export const getNewsDetail = async (contentId: string): Promise<News | null> => {
	const client = getClient();
	if (!client) {
		warnMissingCredentials();
		return null;
	}

	try {
		const item = await client.getListDetail<MicroCMSNewsRaw>({
			endpoint: 'news',
			contentId,
		});

		return normalizeNews(item);
	} catch (error) {
		console.error('microCMS からの news 詳細取得に失敗しました:', error);
		return null;
	}
};

/** 新しい順の一覧から、前後（newer / older）を返す */
export const getNewsNeighbors = async (
	contentId: string,
): Promise<{ newer: NewsNeighbor | null; older: NewsNeighbor | null }> => {
	const list = await getNews();
	const index = list.findIndex((item) => item.id === contentId);

	if (index < 0) {
		return { newer: null, older: null };
	}

	const toNeighbor = (item?: News): NewsNeighbor | null =>
		item
			? {
					id: item.id,
					title: item.title,
					date: item.date,
					thumbnail: item.thumbnail,
				}
			: null;

	return {
		newer: toNeighbor(list[index - 1]),
		older: toNeighbor(list[index + 1]),
	};
};

export const getResearch = async (
	queries: MicroCMSQueries = {},
): Promise<Research[]> => {
	const client = getClient();
	if (!client) {
		warnMissingCredentials();
		return [];
	}

	type ResearchRaw = {
		id?: string;
		title?: string;
		date?: string;
		publishedAt?: string;
		venue?: string;
		role?: string;
		author?: string;
		summary?: string;
		abstract?: string;
		link?: string;
		url?: string;
	};

	const normalize = (item: ResearchRaw, fallbackId = 'research'): Research => ({
		id: item.id || fallbackId,
		title: item.title || '',
		date: item.date || item.publishedAt || '',
		venue: item.venue,
		role: item.role,
		author: item.author,
		summary: item.summary || item.abstract,
		link: item.link || item.url,
	});

	try {
		const data = await client.getList<ResearchRaw>({
			endpoint: 'research',
			queries: {
				limit: 100,
				orders: '-date',
				...queries,
			},
		});

		if (Array.isArray(data.contents)) {
			return data.contents.map((item) => normalize(item));
		}

		// オブジェクト形式 API: getList が単体オブジェクトを返すことがある
		const single = data as unknown as ResearchRaw;
		if (single?.title) {
			return [normalize(single)];
		}

		return [];
	} catch (listError) {
		try {
			const item = await client.getObject<ResearchRaw>({
				endpoint: 'research',
			});
			return item?.title ? [normalize(item)] : [];
		} catch (objectError) {
			console.error(
				'microCMS からの research 取得に失敗しました:',
				listError,
				objectError,
			);
			return [];
		}
	}
};

export const getWorks = (queries: MicroCMSQueries = {}) =>
	getList<Omit<Work, 'id'>>('works', {
		orders: '-date',
		...queries,
	});

/** @deprecated 移行用 */
export const getActivities = (queries: MicroCMSQueries = {}) =>
	getList<Omit<Activity, 'id'>>('activities', {
		orders: '-date',
		...queries,
	});

export const formatStack = (stack?: string | string[]): string => {
	if (!stack) {
		return '';
	}

	if (Array.isArray(stack)) {
		return stack.filter(Boolean).join('、');
	}

	return stack;
};
