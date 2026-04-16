import React from 'react';
import styles from './Card.module.css';
import clsx from 'clsx';

interface CardProps {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
    action?: React.ReactNode;
    className?: string;
    noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({
    children,
    title,
    subtitle,
    action,
    className,
    noPadding = false,
}) => {
    return (
        <div className={clsx(styles.card, className)}>
            {(title || action) && (
                <div className={styles.header}>
                    <div className={styles.titleWrapper}>
                        {title && <h3 className={styles.title}>{title}</h3>}
                        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
                    </div>
                    {action && <div className={styles.action}>{action}</div>}
                </div>
            )}
            <div className={clsx(styles.content, { [styles.noPadding]: noPadding })}>
                {children}
            </div>
        </div>
    );
};
