/**
 * Waitlist Worker for EUComply
 * Collects emails of people interested in EUComply Pro / ComplianceDocs
 * Stores them in KV for later notification when Gumroad goes live.
 */

// Handle CORS preflight
function handleOptions(request) {
  return new Response(null, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") return handleOptions(request);

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