import { Metadata } from 'next';
import { getThread, getProject } from '@/lib/api-server';

export async function generateMetadata({ params }): Promise<Metadata> {
  const { threadId } = await params;
  const fallbackMetaData = {
    title: 'Shared Conversation | Kortix Suna',
    description: 'Replay this Agent conversation on Kortix Suna',
    alternates: {
      canonical: `${window.location.origin}/share/${threadId}`,
    },
    openGraph: {
      title: 'Shared Conversation | Kortix Suna',
      description: 'Replay this Agent conversation on Kortix Suna',
      images: [`${window.location.origin}/share-page/og-fallback.png`],
    },
  };

  try {
    const threadData = await getThread(threadId);
    const projectData = await getProject(threadData.project_id);

    if (!threadData || !projectData) {
      return fallbackMetaData;
    }

    const isDevelopment =
      process.env.NODE_ENV === 'development' ||
      process.env.NEXT_PUBLIC_ENV_MODE === 'LOCAL' ||
      process.env.NEXT_PUBLIC_ENV_MODE === 'local';

    const title = projectData.name || 'Shared Conversation | Kortix Suna';
    const description =
      projectData.description ||
      'Replay this Agent conversation on Kortix Suna';
    const ogImage = isDevelopment
      ? `${window.location.origin}/share-page/og-fallback.png`
      : `${window.location.origin}/api/share-page/og-image?title=${projectData.name}`;

    return {
      title,
      description,
      alternates: {
        canonical: `${window.location.origin}/share/${threadId}`,
      },
      openGraph: {
        title,
        description,
        images: [ogImage],
      },
      twitter: {
        title,
        description,
        images: ogImage,
        card: 'summary_large_image',
      },
    };
  } catch (error) {
    return fallbackMetaData;
  }
}

export default async function ThreadLayout({ children }) {
  return <>{children}</>;
}
