import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import styles from './Manual.module.css';

import manualText from '@/assets/manual.md?raw';

export function Manual() {
  const title = '网络舆情应对手册';

  return (
    <MainLayout>
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>{title}</h1>
        </div>

        <Card className={styles.articleCard}>
          <article className={styles.article}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, rehypeSlug]}
              components={{
                a: ({ node, href, children, ...props }) => {
                  if (href?.startsWith('#')) {
                    return (
                      <a
                        {...props}
                        href={href}
                        onClick={(e) => {
                          e.preventDefault();
                          const id = decodeURIComponent(href.slice(1));
                          const target = document.getElementById(id);
                          if (target) {
                            target.scrollIntoView({ behavior: 'smooth' });
                          }
                        }}
                      >
                        {children}
                      </a>
                    );
                  }
                  return <a href={href} {...props}>{children}</a>;
                }
              }}
            >
              {manualText}
            </ReactMarkdown>
          </article>
        </Card>
      </div>
    </MainLayout>
  );
}
