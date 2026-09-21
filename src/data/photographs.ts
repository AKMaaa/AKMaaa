export type Photograph = {
	id: string;
	title: string;
	year?: string;
	place?: string;
	src: string;
	alt: string;
};

/** 仮画像。差し替えは public/images/photographs/ へ */
export const photographs: Photograph[] = [
	{
		id: 'p1',
		title: 'Untitled #01',
		year: '2025',
		place: 'Hokkaido',
		src: '/images/photographs/01.svg',
		alt: 'photograph placeholder 01',
	},
	{
		id: 'p2',
		title: 'Untitled #02',
		year: '2024',
		place: 'Hakodate',
		src: '/images/photographs/02.svg',
		alt: 'photograph placeholder 02',
	},
	{
		id: 'p3',
		title: 'Untitled #03',
		year: '2024',
		place: 'Osaka',
		src: '/images/photographs/03.svg',
		alt: 'photograph placeholder 03',
	},
];
