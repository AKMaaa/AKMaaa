import { createClient, type MicroCMSQueries } from 'microcms-js-sdk';

export type News = {
	id: string;
	title: string;
	date: string;
	body?: string;
	link?: string;
};

export type Research = {
	id: string;
	title: string;
	date: string;
	venue?: string;
	role?: string;
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

type MicroCMSNewsRaw = {
	title: string;
	date?: string;
	publishedAt?: string;
	body?: string;
	content?: string;
	link?: string;
};

const serviceDomain = import.meta.env.MICROCMS_SERVICE_DOMAIN;
const apiKey = import.meta.env.MICROCMS_API_KEY;

const hasCredentials =
	typeof serviceDomain === 'string' &&
	typeof apiKey === 'string' &&
	serviceDomain.length > 0 &&
	apiKey.length > 0 &&
	!serviceDomain.startsWith('your-') &&
	!apiKey.startsWith('your-');

const client = hasCredentials
	? createClient({
			serviceDomain,
			apiKey,
		})
	: null;

const warnMissingCredentials = () => {
	console.warn(
		'microCMS の認証情報が未設定です。.env の MICROCMS_SERVICE_DOMAIN と MICROCMS_API_KEY を実値に差し替えてください。',
	);
};

const getList = async <T>(
	endpoint: string,
	queries: MicroCMSQueries = {},
): Promise<(T & { id: string })[]> => {
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

		return data.contents;
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

	return contents.map((item) => ({
		id: item.id,
		title: item.title,
		date: item.date || item.publishedAt || '',
		body: item.body || item.content,
		link: item.link,
	}));
};

/** 1件取得: GET /api/v1/news/{contentId} 相当 */
export const getNewsDetail = async (contentId: string): Promise<News | null> => {
	if (!client) {
		warnMissingCredentials();
		return null;
	}

	try {
		const item = await client.getListDetail<MicroCMSNewsRaw>({
			endpoint: 'news',
			contentId,
		});

		return {
			id: item.id,
			title: item.title,
			date: item.date || item.publishedAt || '',
			body: item.body || item.content,
			link: item.link,
		};
	} catch (error) {
		console.error('microCMS からの news 詳細取得に失敗しました:', error);
		return null;
	}
};

export const getResearch = (queries: MicroCMSQueries = {}) =>
	getList<Omit<Research, 'id'>>('research', {
		orders: '-date',
		...queries,
	});

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
