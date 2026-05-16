import type { NextConfig } from "next";

// URUSAI frontend config.
// X-Accel-Buffering: no required for SSE behind nginx / Vercel reverse proxy.
const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/api/threads/:thread/runs/:run/events",
        headers: [
          { key: "X-Accel-Buffering", value: "no" },
          { key: "Cache-Control", value: "no-cache, no-transform" },
        ],
      },
      {
        source: "/api/jobs/:job/events",
        headers: [
          { key: "X-Accel-Buffering", value: "no" },
          { key: "Cache-Control", value: "no-cache, no-transform" },
        ],
      },
    ];
  },
};

export default nextConfig;
