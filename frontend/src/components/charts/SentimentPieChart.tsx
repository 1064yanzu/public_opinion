import React from 'react';
import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';

interface SentimentData {
    name: string;
    value: number;
}

interface SentimentPieChartProps {
    data: SentimentData[]; // Expected: [{name: '正面', value: 10}, ...]
    height?: number;
}

const COLORS = {
    '正面': '#52c41a',
    '中性': '#faad14',
    '负面': '#f5222d',
    '男': '#1890ff',
    '女': '#eb2f96',
    '未知': '#cccccc',
    'positive': '#52c41a',
    'neutral': '#faad14',
    'negative': '#f5222d',
};

export const SentimentPieChart: React.FC<SentimentPieChartProps> = ({
    data,
    height = 300
}) => {
    // Ensure we map standard keys if data uses English keys
    const processedData = data.map(item => {
        let name = item.name;
        if (name === 'positive') name = '正面';
        if (name === 'neutral') name = '中性';
        if (name === 'negative') name = '负面';
        return { ...item, name };
    });

    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <PieChart>
                    <Pie
                        data={processedData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                    >
                        {processedData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={COLORS[entry.name as keyof typeof COLORS] || '#8E8E8E'}
                                strokeWidth={0}
                            />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#FFFFFF',
                            borderRadius: '8px',
                            border: '1px solid #E2E2E0',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                        }}
                    />
                    <Legend
                        verticalAlign="bottom"
                        height={36}
                        iconType="circle"
                        formatter={(value) => <span style={{ color: '#5F5F5F', fontSize: '14px', marginRight: '10px' }}>{value}</span>}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
};
