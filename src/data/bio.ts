export type CareerType = 'employment' | 'parttime' | 'internship' | 'side' | 'education';

export type CareerItem = {
	period: string;
	role: string;
	org: string;
	type: CareerType;
	orgUrl?: string;
	/** ローカルロゴ（`public/images/logos/` 配下） */
	logoPath?: string;
	/** フォールバック用ドメイン（favicon） */
	logoDomain?: string;
	note?: string;
};

export type SkillItem = {
	name: string;
	/** simpleicons.org のスラッグ */
	icon?: string;
	/** ローカルアイコン（`public/` 配下）。icon より優先 */
	iconPath?: string;
};

export type SkillGroup = {
	category: string;
	items: SkillItem[];
};

export type SocialLink = {
	id: 'researchmap' | 'github' | 'facebook';
	label: string;
	url: string;
};

export const careerTypeLabels: Record<'all' | CareerType, string> = {
	all: 'すべて',
	employment: '新卒入社',
	parttime: 'アルバイト',
	internship: 'インターン',
	side: 'サイド',
	education: '学歴',
};

export const careerFilters: Array<'all' | CareerType> = [
	'all',
	'employment',
	'parttime',
	'internship',
	'side',
	'education',
];

export const profileSummary = {
	nameJa: '前田 祥',
	nameEn: 'Maeda Akira',
	lead: 'システム情報科学を背景に、教育・コミュニケーション・Web に関わる制作と実践をしています。本業は Fintech、並行して NPO での教育・広報にも関わっています。',
	based: 'Japan',
};

export const career: CareerItem[] = [
	{
		period: '2026.4 — Present',
		role: '社員',
		org: 'シンプレクス・ホールディングス株式会社',
		orgUrl: 'https://www.simplex.holdings/',
		logoPath: '/images/logos/simplex-holdings.png',
		logoDomain: 'simplex.holdings',
		type: 'employment',
	},
	{
		period: '2023.10 — Present',
		role: '広報 / エンジニア',
		org: '特定非営利活動法人 学び足しデザイン工房',
		orgUrl: 'https://upskillingjp.org/',
		logoPath: '/images/logos/upskilling.png',
		logoDomain: 'upskillingjp.org',
		type: 'side',
	},
	{
		period: '2021.9 — 2026.3',
		role: 'Web Engineer',
		org: 'ハコレコドットコム株式会社',
		orgUrl: 'https://www.hakoreco.com/',
		logoPath: '/images/logos/hakoreco.svg',
		logoDomain: 'hakoreco.com',
		type: 'parttime',
	},
	{
		period: '2025.5 — 2026.3',
		role: 'Engineer',
		org: '株式会社オープンハート',
		orgUrl: 'https://openheart.co.jp/',
		logoPath: '/images/logos/openheart.svg',
		logoDomain: 'openheart.co.jp',
		type: 'parttime',
	},
	{
		period: '2024.8 — 2025.7',
		role: 'Campus Leader',
		org: 'Notion Labs, Inc.',
		orgUrl: 'https://www.notion.so/',
		logoPath: '/images/logos/notion.png',
		logoDomain: 'notion.so',
		type: 'side',
	},
	{
		period: '2025.2 — 2026.3',
		role: 'Trainee',
		org: 'シンプレクス・ホールディングス株式会社',
		orgUrl: 'https://www.simplex.holdings/',
		logoPath: '/images/logos/simplex-holdings.png',
		logoDomain: 'simplex.holdings',
		type: 'internship',
	},
	{
		period: '2024.9',
		role: 'Engineer',
		org: 'シンプレクス・ホールディングス株式会社',
		orgUrl: 'https://www.simplex.holdings/',
		logoPath: '/images/logos/simplex-holdings.png',
		logoDomain: 'simplex.holdings',
		type: 'internship',
	},
	{
		period: '2023.3',
		role: 'UI Designer',
		org: '株式会社サイバーエージェント',
		orgUrl: 'https://www.cyberagent.co.jp/',
		logoPath: '/images/logos/cyberagent.png',
		logoDomain: 'cyberagent.co.jp',
		type: 'internship',
	},
	{
		period: '2023.2',
		role: 'Software Engineer',
		org: 'ソニーセミコンダクタソリューションズ株式会社',
		orgUrl: 'https://www.sony-semiconductor.co.jp/',
		logoPath: '/images/logos/sony.png',
		logoDomain: 'sony-semiconductor.co.jp',
		type: 'internship',
	},
	{
		period: '2022.9',
		role: 'Web Engineer',
		org: '株式会社ナビタイムジャパン',
		orgUrl: 'https://www.navitime.co.jp/',
		logoPath: '/images/logos/navitime.png',
		logoDomain: 'navitime.co.jp',
		type: 'internship',
	},
	{
		period: '2022.9',
		role: 'Designer',
		org: '日本アイ・ビー・エム株式会社',
		orgUrl: 'https://www.ibm.com/jp-ja',
		logoPath: '/images/logos/ibm.png',
		logoDomain: 'ibm.com',
		type: 'internship',
	},
	{
		period: '2022.8',
		role: 'Business Consultant',
		org: '株式会社船井総合研究所',
		orgUrl: 'https://www.funaisoken.co.jp/',
		logoPath: '/images/logos/funai.png',
		logoDomain: 'funaisoken.co.jp',
		type: 'internship',
	},
	{
		period: '2024.4 — 2026.3',
		role: '修士（システム情報科学）',
		org: '公立はこだて未来大学大学院',
		orgUrl: 'https://www.fun.ac.jp/',
		logoPath: '/images/logos/fun-crest.svg',
		logoDomain: 'fun.ac.jp',
		type: 'education',
		note: 'メディアデザイン領域',
	},
	{
		period: '2020.4 — 2024.3',
		role: '学士（システム情報科学）',
		org: '公立はこだて未来大学',
		orgUrl: 'https://www.fun.ac.jp/',
		logoPath: '/images/logos/fun-crest.svg',
		logoDomain: 'fun.ac.jp',
		type: 'education',
		note: '情報デザインコース',
	},
];

export const skills: SkillGroup[] = [
	{
		category: 'Languages',
		items: [
			{ name: 'JavaScript', icon: 'javascript' },
			{ name: 'TypeScript', icon: 'typescript' },
			{ name: 'Python', icon: 'python' },
			{ name: 'Java', icon: 'openjdk' },
			{ name: 'Go', icon: 'go' },
			{ name: 'C', icon: 'c' },
		],
	},
	{
		category: 'Frontend',
		items: [
			{ name: 'React', icon: 'react' },
			{ name: 'Vue.js', icon: 'vuedotjs' },
			{ name: 'HTML', icon: 'html5' },
			{ name: 'CSS', icon: 'css' },
		],
	},
	{
		category: 'Backend',
		items: [
			{ name: 'Node.js', icon: 'nodedotjs' },
			{ name: 'Express', icon: 'express' },
			{ name: 'FastAPI', icon: 'fastapi' },
		],
	},
	{
		category: 'CMS',
		items: [
			{ name: 'WordPress', icon: 'wordpress' },
			{ name: 'microCMS', iconPath: '/images/skills/microcms.svg' },
		],
	},
	{
		category: 'LLM / AI',
		items: [
			{ name: 'OpenAI', iconPath: '/images/skills/openai.svg' },
			{ name: 'Claude', icon: 'anthropic' },
			{ name: 'Gemini', icon: 'googlegemini' },
			{ name: 'LangChain', icon: 'langchain' },
		],
	},
	{
		category: 'Infrastructure',
		items: [
			{ name: 'Google Cloud', icon: 'googlecloud' },
			{ name: 'Cloudflare', icon: 'cloudflare' },
			{ name: 'Docker', icon: 'docker' },
			{ name: 'Linux', icon: 'linux' },
		],
	},
	{
		category: 'Tools',
		items: [
			{ name: 'Git', icon: 'git' },
			{ name: 'Figma', icon: 'figma' },
		],
	},
];

export const socials: SocialLink[] = [
	{
		id: 'researchmap',
		label: 'researchmap',
		url: 'https://researchmap.jp/akira-maeda',
	},
	{
		id: 'github',
		label: 'github',
		url: 'https://github.com/AKMaaa',
	},
	{
		id: 'facebook',
		label: 'facebook',
		url: 'https://www.facebook.com/profile.php?id=100092407533693',
	},
];

export const contactEmail = 'akira.vvs@upskillingjp.org';

export const orgLogoUrl = (item: Pick<CareerItem, 'logoPath' | 'logoDomain'>) => {
	if (item.logoPath) return item.logoPath;
	if (item.logoDomain) {
		return `https://www.google.com/s2/favicons?domain=${item.logoDomain}&sz=128`;
	}
	return '';
};

/** Simple Icons CDN（単色で揃える） */
export const skillIconUrl = (slug: string) =>
	`https://cdn.simpleicons.org/${slug}/57534e`;

export const skillImageUrl = (skill: SkillItem) => {
	if (skill.iconPath) return skill.iconPath;
	if (skill.icon) return skillIconUrl(skill.icon);
	return '';
};
