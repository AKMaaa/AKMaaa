type Env = {
	TURNSTILE_SECRET_KEY: string;
	CONTACT_TO: string;
	THANKS_URL: string;
	ALLOW_ORIGIN?: string;
};

const json = (body: unknown, status = 200, extra: HeadersInit = {}) =>
	new Response(JSON.stringify(body), {
		status,
		headers: {
			'content-type': 'application/json; charset=utf-8',
			...extra,
		},
	});

const html = (body: string, status = 200) =>
	new Response(body, {
		status,
		headers: { 'content-type': 'text/html; charset=utf-8' },
	});

const redirect = (url: string) =>
	new Response(null, {
		status: 303,
		headers: { Location: url },
	});

async function verifyTurnstile(token: string, secret: string, ip: string | null) {
	const body = new URLSearchParams();
	body.set('secret', secret);
	body.set('response', token);
	if (ip) body.set('remoteip', ip);

	const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
		method: 'POST',
		body,
	});
	if (!res.ok) return false;
	const data = (await res.json()) as { success?: boolean };
	return data.success === true;
}

/**
 * FormSubmit はブラウザ Origin 前提。Worker から送るときは Referer を付与し、
 * JSON の success を見る。失敗しやすいので呼び出し側でフォールバックすること。
 */
async function forwardToFormSubmit(
	to: string,
	fields: { name: string; email: string; message: string; subject: string },
	origin: string,
) {
	const body = new URLSearchParams();
	body.set('name', fields.name);
	body.set('email', fields.email);
	body.set('_replyto', fields.email);
	body.set('message', fields.message);
	body.set('_subject', fields.subject);
	body.set('_template', 'table');
	body.set('_captcha', 'false');

	const res = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(to)}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/x-www-form-urlencoded',
			Origin: origin,
			Referer: `${origin}/AKMaaa/contact/`,
		},
		body,
	});

	const text = await res.text();
	try {
		const data = JSON.parse(text) as { success?: boolean | string };
		return data.success === true || data.success === 'true';
	} catch {
		return res.ok;
	}
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const allowOrigin = env.ALLOW_ORIGIN || 'https://akmaaa.github.io';
		const thanks = env.THANKS_URL || 'https://akmaaa.github.io/AKMaaa/contact/?sent=1';
		const errorUrl = thanks.replace('sent=1', 'error=1');

		if (request.method === 'OPTIONS') {
			return new Response(null, {
				status: 204,
				headers: {
					'Access-Control-Allow-Origin': allowOrigin,
					'Access-Control-Allow-Methods': 'POST, OPTIONS',
					'Access-Control-Allow-Headers': 'Content-Type, Accept',
					'Access-Control-Max-Age': '86400',
				},
			});
		}

		if (request.method !== 'POST') {
			return json({ ok: false, error: 'method_not_allowed' }, 405);
		}

		if (!env.TURNSTILE_SECRET_KEY) {
			return json({ ok: false, error: 'misconfigured' }, 500);
		}

		const form = await request.formData();
		const honey = String(form.get('_honey') ?? '').trim();
		if (honey) {
			return redirect(thanks);
		}

		const name = String(form.get('name') ?? '').trim();
		const email = String(form.get('email') ?? '').trim();
		const message = String(form.get('message') ?? '').trim();
		const subject = String(form.get('_subject') ?? 'Portfolio contact — Maeda Akira').trim();
		const mode = String(form.get('_mode') ?? '').trim(); // verify | deliver
		const token = String(
			form.get('cf-turnstile-response') ?? form.get('g-recaptcha-response') ?? '',
		).trim();

		const wantsJson = (request.headers.get('Accept') || '').includes('application/json');

		if (!name || !email || !message || !token) {
			if (wantsJson) return json({ ok: false, error: 'invalid_request' }, 400);
			return redirect(errorUrl);
		}

		const ip = request.headers.get('CF-Connecting-IP');
		const human = await verifyTurnstile(token, env.TURNSTILE_SECRET_KEY, ip);
		if (!human) {
			if (wantsJson) return json({ ok: false, error: 'turnstile_failed' }, 403);
			return redirect(errorUrl);
		}

		// フロントが FormSubmit に渡す前の検証のみ
		if (mode === 'verify') {
			return json(
				{ ok: true },
				200,
				{ 'Access-Control-Allow-Origin': allowOrigin },
			);
		}

		const sent = await forwardToFormSubmit(
			env.CONTACT_TO,
			{ name, email, message, subject },
			allowOrigin,
		);

		if (!sent) {
			if (wantsJson) return json({ ok: false, error: 'delivery_failed' }, 502);
			return redirect(errorUrl);
		}

		if (wantsJson) {
			return json({ ok: true }, 200, { 'Access-Control-Allow-Origin': allowOrigin });
		}

		return redirect(thanks);
	},
} satisfies ExportedHandler<Env>;
