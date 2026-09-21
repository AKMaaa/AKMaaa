export type Hobby = {
	id: string;
	title: string;
	summary: string;
};

export const hobbies: Hobby[] = [
	{
		id: 'music',
		title: 'Music',
		summary: '聴くこと・見つけること。気分や季節でプレイリストを組み替えるのが好きです。',
	},
	{
		id: 'coffee',
		title: 'Coffee',
		summary: '淹れるのも飲むのも好きです。お店めぐりや豆選びも楽しみのひとつです。',
	},
	{
		id: 'photo',
		title: 'Photography',
		summary: '街や風景をゆっくり撮ります。作品は photographs に置いています。',
	},
	{
		id: 'walk',
		title: 'Walking',
		summary: '知らない路地や港まわりを歩くのが好きです。',
	},
	{
		id: 'reading',
		title: 'Reading',
		summary: 'デザイン、教育、小説をときどき。',
	},
];
