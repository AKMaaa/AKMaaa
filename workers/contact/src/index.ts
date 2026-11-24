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

async function forwardToFormSubmit(
	to: string,
	fields: { name: string; email: string; message: string; subject: string },
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
		},
		body,
	});

	return res.ok;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const allowOrigin = env.ALLOW_ORIGIN || '*';

		if (request.method === 'OPTIONS') {
			return new Response(null, {
				status: 204,
				headers: {
					'Access-Control-Allow-Origin': allowOrigin,
					'Access-Control-Allow-Methods': 'POST, OPTIONS',
					'Access-Control-Allow-Headers': 'Content-Type',
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
			// ボットは成功したふりをして終わる
			return redirect(env.THANKS_URL);
		}

		const name = String(form.get('name') ?? '').trim();
		const email = String(form.get('email') ?? '').trim();
		const message = String(form.get('message') ?? '').trim();
		const subject = String(form.get('_subject') ?? 'Portfolio contact — Maeda Akira').trim();
		const token = String(
			form.get('cf-turnstile-response') ?? form.get('g-recaptcha-response') ?? '',
		).trim();

		if (!name || !email || !message || !token) {
			return json({ ok: false, error: 'invalid_request' }, 400);
		}

		const ip = request.headers.get('CF-Connecting-IP');
		const human = await verifyTurnstile(token, env.TURNSTILE_SECRET_KEY, ip);
		if (!human) {
			return json({ ok: false, error: 'turnstile_failed' }, 403);
		}

		const sent = await forwardToFormSubmit(env.CONTACT_TO, {
			name,
			email,
			message,
			subject,
		});

		if (!sent) {
			return json({ ok: false, error: 'delivery_failed' }, 502);
		}

		const wantsJson = (request.headers.get('Accept') || '').includes('application/json');
		if (wantsJson) {
			return json(
				{ ok: true },
				200,
				{ 'Access-Control-Allow-Origin': allowOrigin },
			);
		}

		return redirect(env.THANKS_URL);
	},
} satisfies ExportedHandler<Env>;
