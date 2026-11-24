export type Photograph = {
	id: string;
	title: string;
	year?: string;
	place?: string;
	src: string;
	alt: string;
	width: number;
	height: number;
	/** グリッドで横いっぱいに見せる */
	featured?: boolean;
};

export const photographs: Photograph[] = [
	{
		id: 'hydrangea',
		title: 'Hydrangea',
		src: '/images/photographs/01-hydrangea.webp',
		alt: 'むらさきがかった紫陽花のクローズアップ',
		width: 1024,
		height: 682,
		featured: true,
	},
	{
		id: 'gallery',
		title: 'At the gallery',
		src: '/images/photographs/02-gallery.webp',
		alt: '黒い壁に飾られた猫の着ぐるみの絵',
		width: 682,
		height: 1024,
	},
	{
		id: 'salon',
		title: 'Salon light',
		src: '/images/photographs/03-salon.webp',
		alt: 'ドライフラワーと絵画が並ぶ室内',
		width: 1024,
		height: 682,
	},
	{
		id: 'towers',
		title: 'Looking up',
		src: '/images/photographs/04-towers.webp',
		alt: 'ガラスの高層ビルを見上げた構図',
		width: 1024,
		height: 682,
	},
	{
		id: 'cat',
		title: 'On the wall',
		src: '/images/photographs/05-cat.webp',
		alt: 'レンガ壁の上に座る白と茶色の猫',
		width: 1024,
		height: 682,
	},
	{
		id: 'fallen-leaves',
		title: 'Fallen leaves',
		src: '/images/photographs/06-fallen-leaves.webp',
		alt: '落ち葉の道に立つ足元',
		width: 1024,
		height: 682,
	},
];
