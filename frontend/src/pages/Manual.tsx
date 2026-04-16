import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Loading } from '@/components/common/Loading';
import { fetchManualContent } from '@/services/page';
import styles from './Manual.module.css';

export function Manual() {
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('舆情应对手册');
  const [markdown, setMarkdown] = useState('');
  const [sourcePath, setSourcePath] = useState('');

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      const response = await fetchManualContent();
      if (!mounted) {
        return;
      }
      setTitle(response.title);
      setMarkdown(response.markdown);
      setSourcePath(response.source_path);
      setLoading(false);
    };

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return <Loading fullScreen text="正在读取手册正文..." />;
  }

  return (
    <MainLayout>
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>{title}</h1>
          <p className={styles.subtitle}>Markdown 正文已按真实文档结构渲染，不再做伪解析。</p>
          <p className={styles.meta}>来源：{sourcePath}</p>
        </div>

        <Card className={styles.articleCard}>
          <article className={styles.article}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
            >
              {markdown}
            </ReactMarkdown>
          </article>
        </Card>
      </div>
    </MainLayout>
  );
}
