import React from 'react';
import styles from './Loading.module.css';
import { Loader2 } from 'lucide-react';

interface LoadingProps {
    text?: string;
    fullScreen?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({ text = '加载中...', fullScreen = false }) => {
    if (fullScreen) {
        return (
            <div className={styles.fullScreenOverlay}>
                <div className={styles.container}>
                    <Loader2 className={styles.spinner} size={32} />
                    <p className={styles.text}>{text}</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <Loader2 className={styles.spinner} size={24} />
            <span className={styles.text}>{text}</span>
        </div>
    );
};
