/**
 * Waitlist Worker for EUComply
 * Collects emails of people interested in EUComply Pro / ComplianceDocs
 * Stores them in KV for later notification when Lemon Squeezy checkout goes live.
 */

// Handle CORS preflight
function handleOptions(request) {
  return new Response(null, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

// ── GET handler: returns waitlist count (social proof for sales pages) ──
async function handleGetCount(env) {
  try {
    const list = await env.WAITLIST.list({ prefix: "by_time:" });
    const count = list.keys.length;
    return new Response(JSON.stringify({ count, status: "ok" }), {
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=60",  // 1 min cache — fresh enough for live display
      },
    });
  } catch (err) {
    return new Response(JSON.stringify({ count: 0, status: "error", detail: err.message }), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }
}

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") return handleOptions(request);

    // GET /config → return checkout URL for dynamic checkout buttons
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/config") {
      return new Response(JSON.stringify({
        service: "quickformat-waitlist",
        checkout_url: (env.CHECKOUT_URL || "").trim(),
      }), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=60",
        },
      });
    }

    // GET request → return waitlist count (social proof)
    if (request.method === "GET") {
      return handleGetCount(env);
    }

    // Only accept POST
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      });
    }

    try {
      const body = await request.json();
      const email = body.email?.trim().toLowerCase();

      // Validate email
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return new Response(JSON.stringify({ error: "Valid email is required" }), {
          status: 400,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }

      // Reserverede testdomaener maa ALDRIG lande i ventelisten: de kan pr.
      // definition ikke modtage post, og de blev tidligere talt med som
      // rigtige tilmeldinger, saa status rapporterede 6 personer ved 0 rigtige.
      const TESTDOMAENER = /@(example\.(com|org|net)|test\.com|localhost)$/i;
      if (TESTDOMAENER.test(email)) {
        return new Response(JSON.stringify({
          message: "Test accepted (not stored)", test: true,
        }), {
          status: 200,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }

      // Check for double signup
      const existing = await env.WAITLIST.get(email);
      if (existing) {
        return new Response(JSON.stringify({ message: "You're already on the list!" }), {
          status: 200,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }

      // Store email with timestamp
      const entry = JSON.stringify({
        email,
        signed_up_at: new Date().toISOString(),
        source: body.source || "eucomply-landing",
      });
      await env.WAITLIST.put(email, entry);

      // Also maintain a reverse-index by timestamp for easy listing
      const timestamp = Date.now().toString();
      await env.WAITLIST.put(`by_time:${timestamp}`, email);

      return new Response(JSON.stringify({ message: "You're on the list! We'll let you know when payment opens." }), {
        status: 200,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: "Invalid request" }), {
        status: 400,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      });
    }
  },
};