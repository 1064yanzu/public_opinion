import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import styles from './Sidebar.module.css';
import {
    LayoutDashboard,
    BarChart,
    Search,
    FileText,
    Settings,
    MessageSquare,
    Activity,
    LogOut,
    DatabaseZap,
    Radar,
    BookOpen,
    LibraryBig
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';

const NAV_ITEMS = [
    { path: '/', label: '概览', icon: LayoutDashboard },
    { path: '/spider', label: '爬虫控制', icon: DatabaseZap },
    { path: '/analysis', label: '舆情分析', icon: Search },
    { path: '/advanced', label: '高级洞察', icon: BarChart },
    { path: '/bigdata', label: '数据看板', icon: Radar },
    { path: '/cases', label: '案例库', icon: LibraryBig },
    { path: '/manual', label: '应对手册', icon: BookOpen },
    { path: '/reports', label: '报告生成', icon: FileText },
    { path: '/monitor', label: '系统监控', icon: Activity },
    { path: '/ai-assistant', label: 'AI 助手', icon: MessageSquare },
    { path: '/settings', label: '设置', icon: Settings },
];

export const Sidebar: React.FC = () => {
    const { logout } = useAuth();
    const location = useLocation();

    return (
        <aside className={styles.sidebar}>
            <div className={styles.logo}>
                <div className={styles.logoIcon} />
                <span className={styles.logoText}>舆情洞察</span>
            </div>

            <nav className={styles.nav}>
                {NAV_ITEMS.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => clsx(styles.navItem, isActive && styles.active)}
                        >
                            <Icon size={20} className={styles.icon} />
                            <span className={styles.label}>{item.label}</span>
                            {isActive && <div className={styles.activeIndicator} />}
                        </NavLink>
                    );
                })}
            </nav>

            <div className={styles.footer}>
                <button onClick={logout} className={styles.logoutButton}>
                    <LogOut size={18} />
                    <span>退出登录</span>
                </button>
            </div>
        </aside>
    );
};
