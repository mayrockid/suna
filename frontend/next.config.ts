import type { NextConfig } from 'next';

const nextConfig = (): NextConfig => ({
  output: (process.env.NEXT_OUTPUT as 'standalone') || undefined,
  async rewrites() {
    return [
      {
        source: `${process.env.NEXT_PUBLIC_BACKEND_URL}/:path*`,
        destination: 'http://192.168.1.181:8000/api/:path*',
      },
    ];

  }
});

export default nextConfig;
