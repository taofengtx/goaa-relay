/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  productionBrowserSourceMaps: false,
  output: 'standalone',
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/aika-download',
          destination: '/aika-download.html',
        },
      ],
    }
  },
}

module.exports = nextConfig
