/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker multi-stage builds
  output: "standalone",

  // Allow Next.js server components to call the backend internally
  async rewrites() {
    const internalApiUrl =
      process.env.NEXT_INTERNAL_API_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      (process.env.NODE_ENV === "production"
        ? "https://memory-leak-api.onrender.com/api/v1"
        : process.env.NEXT_INTERNAL_API_HOSTPORT
          ? `http://${process.env.NEXT_INTERNAL_API_HOSTPORT}/api/v1`
          : "http://localhost:8000/api/v1");

    return [
      {
        source: "/api/v1/:path*",
        destination: `${internalApiUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
